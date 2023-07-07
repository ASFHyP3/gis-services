from lxml import etree

service_draft = r'C:\Users\hjkristenson\PycharmProjects\gis-services\image_services\rtc_services\USDA_RTC_VV_230707_0039.sddraft'
service_draft_out = r'C:\Users\hjkristenson\PycharmProjects\gis-services\image_services\rtc_services\USDA_RTC_VV_test.sddraft'

tree = etree.parse(service_draft)

extensions = tree.find("/Configurations/SVCConfiguration/Definition/Extensions")

xsi_type = etree.QName("http://www.w3.org/2001/XMLSchema-instance", "type")

svc_extension = etree.SubElement(extensions, 'SVCExtension', {xsi_type: 'typens:SVCExtension'})

svc_ext_elements = [('Enabled', '', ''), ('Info', {xsi_type: 'typens:PropertySet'}),
            ('Props', {xsi_type: 'typens:PropertySet'}), ('TypeName', '', '')]

for sub_el in svc_ext_elements:
    if sub_el[1] == '':
        etree.SubElement(svc_extension, sub_el[0])
    else:
        etree.SubElement(svc_extension, sub_el[0], sub_el[1])
        sub_el_path = tree.find(f"/Configurations/SVCConfiguration/Definition/Extensions/SVCExtension/{sub_el[0]}")
        etree.SubElement(sub_el_path, 'PropertyArray', {xsi_type: 'typens:ArrayOfPropertySetProperty'})

tree.find("/Configurations/SVCConfiguration/Definition/Extensions/SVCExtension/Enabled").text = 'true'

sub_props = tree.find("/Configurations/SVCConfiguration/Definition/Extensions/SVCExtension/Info/PropertyArray")
for el in [('WebEnabled', 'true'),
           ('WebCapabilities', 'GetCapabilities,GetMap,GetFeatureInfo,GetStyles,GetLegendGraphic,GetSchemaExtension')]:
    add_prop = etree.SubElement(sub_props, 'PropertySetProperty', {xsi_type: 'typens:PropertySetProperty'})
    key = etree.SubElement(add_prop, 'Key')
    key.text = el[0]
    value = etree.SubElement(add_prop, 'Value', {xsi_type: 'xs:string'})
    value.text = el[1]

# sub_props = tree.find("/Configurations/SVCConfiguration/Definition/Extensions/SVCExtension/Props/PropertyArray")
# for el in range(21):
#     add_prop = etree.SubElement(sub_props, 'PropertySetProperty', type='typens:PropertySetProperty')
#     etree.SubElement(sub_props, 'PropertySetProperty', type='typens:PropertySetProperty')
#     etree.SubElement(add_prop, 'Key')
#     etree.SubElement(add_prop, 'Value', type='xs:string')

tree.find("/Configurations/SVCConfiguration/Definition/Extensions/SVCExtension/TypeName").text = 'WMSServer'

tree.write(service_draft_out)
