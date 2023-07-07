from lxml import etree

service_draft = r'C:\Users\hjkristenson\PycharmProjects\gis-services\image_services\rtc_services\USDA_RTC_VV_230707_0039.sddraft'
service_draft_out = r'C:\Users\hjkristenson\PycharmProjects\gis-services\image_services\rtc_services\USDA_RTC_VV_test.sddraft'

tree = etree.parse(service_draft)
sub_el_extensions = tree.find("/Configurations/SVCConfiguration/Definition/Extensions")
sub_el_svcextension = etree.SubElement(sub_el_extensions, 'SVCExtension', type='typens:SVCExtension',
                                       nsmap={'xsi':'http://www.w3.org/2001/XMLSchema-instance'})

svc_exts = [('Enabled', '', ''), ('Info', 'typens:PropertySet', {'xsi':'http://www.w3.org/2001/XMLSchema-instance'}),
            ('Props', 'typens:PropertySet', {'xsi':'http://www.w3.org/2001/XMLSchema-instance'}), ('TypeName', '', '')]
for sub_el in svc_exts:
    if sub_el[1] == '':
        etree.SubElement(sub_el_svcextension, sub_el[0])
    else:
        etree.SubElement(sub_el_svcextension, sub_el[0], type=sub_el[1], nsmap=sub_el[2])
        sub_el_path = tree.find(f"/Configurations/SVCConfiguration/Definition/Extensions/SVCExtension/{sub_el[0]}")
        etree.SubElement(sub_el_path, 'PropertyArray', type='typens:ArrayOfPropertySetProperty')

sub_el_info_props = tree.find("/Configurations/SVCConfiguration/Definition/Extensions/SVCExtension/Info/PropertyArray")


tree.write(service_draft_out)
