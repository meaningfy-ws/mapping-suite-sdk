from mssdk.core.models.core import XMLTestDataFile


def test_field_validator_inheritance_of_abstract_method(example_xml_content: str):
    subclass_instance = XMLTestDataFile(suite_name="eforms_1.9",
                                        name="my_file.xml",
                                        content="example_xml_content")

    print(subclass_instance)
