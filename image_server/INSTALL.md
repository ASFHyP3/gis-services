This Documentation describes the way to deploy the arcGIS server on the Amazon cloud and configure the server.
It also introduces how to publish the gdb dataset. 


## Reference 

https://enterprise.arcgis.com/en/server/latest/install/linux/install-arcgis-server-on-one-machine.htm
Tools NASA Disasters GitHub repo:
https://github.com/ASFHyP3/hyp3-nasa-disasters/tree/main/update_image_services

## Prepare the Deployment

Find the “Esri ArcGIS Enterprise 10.9.1 on Ubuntu (Dec 2021)” AMI in the EC2 console

Visit the AWS Marketplace and subscribe to the product
https://aws.amazon.com/marketplace/server/procurement?productId=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
You will need to log in under your organization’s account; the organization is subscribing, not the individual user.

Upload an SSL certificate into AWS ACM
The same Tools certificate can be used for any of our deployments

Import a public key in the AWS EC2 console
Existing users can add keys for additional users so that they can SSH in

## Deploy the stack

CloudFormation template is at https://github.com/ASFHyP3/hyp3-nasa-disasters/blob/main/update_image_services/image_server_cloudformation.yml
Can deploy either from command line or the AWS CloudFormation console
ImageId would be different for 10.8.1 vs 10.9.1
Choose the appropriate image for the appropriate Ubuntu version
Keep defaults on acknowledgement page
Takes about 5 minutes to stands up the instance and load balancer
Load balancer will become more critical if we add additional servers


## Configure the Server

Scp the prvc file to the server

10.9.1:
scp ArcGISImageServer_ArcGISServer_1097915.prvc ubuntu@ec2-xx-xxx-xx-xx.us-west-x.compute.amazonaws.com:/home/ubuntu

10.8.1:
scp ArcGISImageServer_ArcGISServer_xxxxxxxx.prvc

ssh to the instance
ssh ubuntu@ec2-xx-xxx-xx-xx.us-west-x.compute.amazonaws.com

The administrative stuff is done under the ubuntu username:
Wait a few minutes for auto-updater stuff to run, then
Sudo apt update
Sudo apt upgrade
Sudo apt autoremove (optional)

(accepts the default table prompts)

Image server is installed and owned by the arcgis username:
su to the arcgis user
sudo su arcgis

Image Server is installed in different directories between the 10.8.1 AMI and the 10.9.1 AMI:
10.8.1 is under /arcgis
10.9.1 is under /opt/arcgis

Authorize the image server software (drop the opt/ for 10.8.1 in the following commands)
/opt/arcgis/server/tools/authorizeSoftware -f /home/ubuntu/ArcGISImageServer_ArcGISServer_xxxxxxx.prvc -e your_email_address

Starting the ArcGIS Software Authorization Wizard

Run this script with -h for additional information

|Product    |Ver            |ECP#          |Expires | 
|:----------|:--------------|:-------------|-------:|
|arcsdeserver|     109      |  ecp075075537|   none |   
|imgsvr      |     109      |  ecp075075537|   none |   
|imgsvr_4    |     109      |  ecp075075537|   none |   

Create a directory to be used later as a raster store (same for 10.8 and 10.9)
At this point, we just need to create a directory. It’s configured as a raster_store later in the configuration process
mkdir /home/arcgis/raster_store

Exit back to being ubuntu and Start/enable the service so Image Server runs automatically at startup (currently the image server doesn’t start when you boot the machine)

Copy a service definition provided by Esri (text file identifying utility scripts for starting and stopping the server). Once this is in place, systemctl administers startup functionality:

sudo cp /opt/arcgis/server/framework/etc/scripts/arcgisserver.service /etc/systemd/system/arcgisserver.service
sudo chmod 600 /etc/systemd/system/arcgisserver.service
sudo systemctl enable arcgisserver.service

We can also manually start it:
sudo systemctl start arcgisserver.service

To check that it’s actually running:
sudo systemctl status arcgisserver.service

Esri made an error in the firewall configuration, which needs to be fixed (port 6080 is listed as 8080 in the image):
Edit iptables rules to redirect ports 80/443 to 6080/6443
sudo vi /etc/iptables/rules.v4
-A PREROUTING -i ens5 -p tcp -m tcp --dport 80 -j REDIRECT --to-ports 6080
-A PREROUTING -i ens5 -p tcp -m tcp --dport 443 -j REDIRECT --to-ports 6443
-A OUTPUT -o lo -p tcp -m tcp --dport 80 -j REDIRECT --to-ports 6080
-A OUTPUT -o lo -p tcp -m tcp --dport 443 -j REDIRECT --to-ports 6443

Restart the server 
sudo shutdown -r now

## Configure Image Server

Load balancer is connected (10.8.1): load_balance_url

Visit the server URL
load_balace_url/arcgis/manager/

Create new site
Pick a password for the siteadmin user, or use the existing password from the tools user
accounts secret
We’ve been using the same siteadmin credentials for all image server deployments
Default directories
If you get a Failed to create the site message, it means that the firewall fix didn’t work

When the progress bar finishes, it might send you back to the “click Finish to create your site” prompt. Just refresh the site and go to /manager, and it should be successfully set up.

Log into management app with siteadmin credentials
Create an administrator role
Security -> roles -> new role


Each user will have an individual account, separate from the siteadmin user
Create admin user accounts
Security -> users -> new user

Once you have an individual account, log out from siteadmin and log in as your individual user.

Register the raster store directory
Site -> data stores -> register -> raster store

The raster_store is just a directory on the server path, so we can use the File Share type.

Configure Image Services

* OPTIONAL: Install miniconda.
For 10.9 we can also just use the python installation bundled with the server, which includes arcpy. For 10.8, the included version of python is 2.7, so we would need to use a conda environment.
sudo su arcgis
cd /home/arcgis
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
bash Miniconda3-latest-Linux-x86_64.sh
rm Miniconda3-latest-Linux-x86_64.sh
Relog (source ~/.bashrc)

* Clone the github repository
cd /home/arcgis
git clone https://github.com/ASFHyP3/hyp3-nasa-disasters.git

* Create the conda environment (the yml in the file is for 10.8; adjust as necessary)
conda env create -f /home/arcgis/hyp3-nasa-disasters/update_image_services/environment.yml

* Upload geodatabase to ubuntu user’s home directory
scp RTCservices_220105.gdb.zip ubuntu@ec2-xx-xxx-xx-xxx.us-west-x.compute.amazonaws.com:/home/ubuntu/
ssh ubuntu@ec2-xx-xxx-xx-xxx.us-west-x.compute.amazonaws.com
unzip directory is not installed by default; need to install:
sudo apt install unzip
unzip unzip RTCservices_220105.gdb.zip

* Change to the arcgis user to copy the unzipped gdb to the RTCservices directory:
sudo su arcgis
cd /home/arcgis
mkdir RTCservices
cp -R /home/ubuntu/RTCservices_220105.gdb /home/arcgis/RTCservices/RTCservices.gdb

* Run publish_service_definitions.py
conda activate arcpy
python /home/arcgis/hyp3-nasa-disasters/update_image_services/publish_service_definitions.py

* Create Service utility info: 
https://enterprise.arcgis.com/en/server/10.8/administer/linux/create-service-utility.htm
https://enterprise.arcgis.com/en/server/latest/develop/linux/create-service-utility.htm
Alas, 10.8 requires that both HTTP and HTTPS be enabled. That constraint is gone in 10.9.
/opt/arcgis/server/tools/admin/createservice -u <username> -p <password> -f /home/arcgis/RTCservices/ASF_S1_RGB.sd -F ASF_S1 -n ASF_S1_RGB

* Publish service definitions

* Create a DNS entry for the load balancer

