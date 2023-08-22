# Publishing and Updating Web Maps in EGIS

Web maps presenting services published to EGIS should be published in the EGIS Portal. This documentation will use the GSSICB dataset as an example to walk through the workflow.

## Publish a New Web Map in EGIS

1. Navigate to https://gis.earthdata.nasa.gov/portal/home/ and log in with the ASF_Publisher credential for the production portal.
![EGIS Map tab](images/egis-map-tab.png)
2. Click on the **Map** tab to open a blank Web Map
3. Click the link to open the map in Map Viewer
   ![Open in Map Viewer](images/egis-map-viewer.png)
4. Click on the **Save and Open** icon and choose the **Save As** option
   ![Save Map and Open](images/egis-save-map.PNG)
5. Complete the fields in the **Save map** dialog box, and click the **Save** button
   ![Save Map Dialog](images/egis-save-details.PNG)

By default, the sharing settings will be for the owner of the map only. Do not change these share settings until the map is ready for public use. Refer to the [Share a Web Map section](#share-a-web-map) for sharing instructions.

## Add Services to a Web Map

Once a GSSICB image service has been published and shared with the public, it should be added to the [Global Seasonal Sentinel-1 Interferometric Coherence and Backscatter webmap](https://gis.earthdata.nasa.gov/portal/apps/mapviewer/index.html?webmap=fe536528ccf341159ef9ad4a50b1c94e).

To ensure that the services are all presented consistently, use the following workflow.

*Use the **Save** button frequently when working with the map, so that you don't lose your work if something causes an interruption or browser refresh.*

### Add Layer from URL

1. Click the layers icon in the map
   ![Add Service from URL](images/egis-add-url.png)
2. Click the drop-down icon next to the **Add** button, and select the option to **Add layer from URL**
3. Enter the URL for the service REST endpoint in the URL field, and click the **Add to map** button
   ![Add Service Layer from URL](images/egis-add-url-layer.PNG)
   - You can find the service URL by searching for the service in the portal, opening the Item Description, and either scrolling to the bottom and clicking the **Copy** button in the URL section or clicking the link to the REST endpoint in the Layers section.
   ![Find Service Layer URL](images/egis-item-desc-url.png)

### Create a Layer Group

The GSSICB services are grouped by season. When adding the first service of a given data type, create a group will also contain the other three seasons for that data type once they are added.

1. Click the dots next to the layer name and select **Group** from the list of options
   ![Add Group](images/egis-add-group.png)
2. Click the dots next to the group name, select **Rename** from the list of options, and enter the desired group title
   ![Rename Group](images/egis-rename-group.png)
3. Add the services for the remaining seasons in the group using the steps in the [Add Layer from URL section](#add-layer-from-url) , and drag and drop the layers to add them into the group in seasonal order: 
   - Dec/Jan/Feb
   - Mar/Apr/May
   - Jun/Jul/Aug
   - Sep/Oct/Nov
   ![Group Contents](images/egis-group-contents.PNG)

### Set Field Properties

In most cases, the properties for numeric fields will need to be edited to display the desired number of decimal places in the pop-ups. Numeric fields tend to default to 0 decimal places in the new Map Viewer, which is problematic for values such as backscatter or unscaled coherence. 

1. Click on a layer once so that it is highlighted with a blue line along the left edge
   ![Set Decimal Places](images/egis-significant-digits.png)
2. Click on the **Fields** icon in the panel along the far right of the browser screen, and select the field that requires the settings to be changed
   - for GSSICB services, only the Unscaled Coherence field will need to be adjusted
3. Use the dropdown menu under **Significant digits** to set the desired number of decimal places to be displayed
   - for GSSICB services, the Unscaled Coherence field should be set to display 2 decimal places
4. Click the Done button to apply the settings

### Format Pop-Ups

   




## Share a Web Map
