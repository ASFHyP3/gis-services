from lxml import etree

service_draft = r'C:\Users\hjkristenson\PycharmProjects\gis-services\image_services\rtc_services\USDA_RTC_VV_230707_0039.sddraft'
service_draft_out = r'C:\Users\hjkristenson\PycharmProjects\gis-services\image_services\rtc_services\USDA_RTC_VV_test.sddraft'

XHTML_NAMESPACE = 'http://www.w3.org/2001/XMLSchema-instance'
XHTML = "{%s}" % XHTML_NAMESPACE
NSMAP = {None : XHTML_NAMESPACE}

tree = etree.parse(service_draft)
sub_el_extensions = tree.find("/Configurations/SVCConfiguration/Definition/Extensions")
sub_el_svcextension = etree.SubElement(sub_el_extensions, 'SVCExtension', type='typens:SVCExtension',
                                       nsmap=NSMAP)

svc_exts = [('Enabled', '', ''), ('Info', 'typens:PropertySet', {'xsi':'http://www.w3.org/2001/XMLSchema-instance'}),
            ('Props', 'typens:PropertySet', {'xsi':'http://www.w3.org/2001/XMLSchema-instance'}), ('TypeName', '', '')]
for sub_el in svc_exts:
    if sub_el[1] == '':
        etree.SubElement(sub_el_svcextension, sub_el[0])
    else:
        etree.SubElement(sub_el_svcextension, sub_el[0], type=sub_el[1], nsmap=sub_el[2])
        sub_el_path = tree.find(f"/Configurations/SVCConfiguration/Definition/Extensions/SVCExtension/{sub_el[0]}")
        etree.SubElement(sub_el_path, 'PropertyArray', type='typens:ArrayOfPropertySetProperty')
        print(f'nsmap={sub_el[2]}')

sub_el_info_props = tree.find("/Configurations/SVCConfiguration/Definition/Extensions/SVCExtension/Info/PropertyArray")
for i in range(2):
    etree.SubElement(sub_el_info_props, 'PropertySetProperty', type='typens:PropertySetProperty')

sub_el_props_props = tree.find("/Configurations/SVCConfiguration/Definition/Extensions/SVCExtension/Props/PropertyArray")
for i in range(21):
    etree.SubElement(sub_el_props_props, 'PropertySetProperty', type='typens:PropertySetProperty')

# It might be easier to just use the Element Maker to construct this whole section, then insert it into the sddraft
# after it's been amended as currently done. But maybe it wouldn't be easier.

# I'm having a hard time figuring out how to get the namespace recognized for the type attributes.
# each of the attributes should be prefaced with xsi:, but I haven't found a way to make that happen yet.

tree.write(service_draft_out)
