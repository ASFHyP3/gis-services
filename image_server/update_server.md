# Updating an ArcGIS Image Server
This document describes the workflow for updating an existing ArcGIS Server with Image Server on AWS EC2 instance to a recent release of ArcGIS Server.

## Upgrading the Server
1. Go to my.esri.com and download the latest version of 
    - ArcGIS Server
    - Portal for ArcGIS
    - ArcGIS Data Store
    - ArcGIS GeoEvent Server
and copy over to the server.
2. Ensure that your OS requirements are up-to-date. See the system requirements [here.](https://enterprise.arcgis.com/en/system-requirements/latest/linux/arcgis-server-system-requirements.htm) If you need to update the operating system, follow [these steps](TODO: Add in section link here)
3. Ensure you are logged in as the `arcgis` user, then install Portal for ArcGIS first with the following commands
```
cd $Portal-installation-dir/
./Setup
```
TODO: There is likely more to this configuration. The install guide is here: https://enterprise.arcgis.com/en/portal/11.4/install/linux/upgrade-portal-for-arcgis.htm

4. Install ArcGIS Server and authorize the installation. TODO: Make sure the `arcgis_setup.sh` is ready to go and see what we can combine from here to there. 
```cd
cd $Server-installation-dir/
./Setup
/opt/arcgis/server/tools/authorizeSoftware -f 11_5/ArcGISImageServer_ArcGISServer_1561174.prvc -e hjkristenson@alaska.edu
```
You can check the installation with 
```
/opt/arcgis/server/tools/authorizeSoftware -s
```

## Upgrading the OS
If the server's OS does not meet the requirements for the latest version of ArcGIS Server, the easiest option is to log in as the root user and upgrade with 
`sudo do-release-upgrade -f DistUpgradeView=Text`.

If your OS is too outdated (i.e. <22.04), you might need to go through a couple of steps before getting the right version. 
`sudo apt update && sudate apt upgrade -y`
Open `sudo vim /etc/update-manager/release-upgrades` and change the `Prompt` value, so that `Prompt=normal`.
You can then upgrade with 
`sudo do-release-upgrade -f DistUpgradeView=Text`

After the server restarts, 
`sudo apt install update-manager-core`
and open `sudo vim /etc/update-manager/release-upgrades` and make sure that `Prompt=Lts`. 
Then, you can run 
`sudo do-release-upgrade -f DistUpgradeView=Text`
Again. 

After the server restarts, there might be an opportunity to upgrade to v24.04 LTS, and the required prompt with display in the welcome text. 



