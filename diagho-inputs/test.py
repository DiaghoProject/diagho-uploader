import unittest
import json
from datetime import datetime
from io import StringIO
from unittest.mock import patch, mock_open


from diagho_inputs import *
from functions import *


class TestDiaghoTsv2Json(unittest.TestCase):
    
    def setUp(self):
        self.input_file = "tests/test_input.tsv"
        self.output_file = "tests/test_output.json"
        

    # def tearDown(self):
    #     # Remove test files if they exist
    #     if os.path.exists(self.input_file):
    #         os.remove(self.input_file)
    #     if os.path.exists(self.output_file):
    #         os.remove(self.output_file)

    def test_diagho_tsv2json(self):
        self.assertEqual.__self__.maxDiff = None
        
        diagho_tsv2json(self.input_file, self.output_file)

        ## Load the TSV input file
        with open(self.output_file, 'r', encoding='utf-8') as f:
            result = json.load(f)
        
        ## Compare with expected result in the JSON file
        with open('tests/test_output_expected_results.json') as json_file:
            expected_result = json.load(json_file)

        self.assertEqual(result, expected_result)


class TestRemoveTrailingEmptyLines(unittest.TestCase):

    def setUp(self):
        self.file_path = 'tests/test_file.txt'
    
    # def tearDown(self):
    #     if os.path.exists(self.file_path):
    #         os.remove(self.file_path)

    def test_remove_trailing_empty_lines(self):
        content = "Line 1\nLine 2\n\nLine 3\n\n\n"
        expected_content = "Line 1\nLine 2\nLine 3\n"

        with open(self.file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        remove_trailing_empty_lines(self.file_path, 'utf-8')

        with open(self.file_path, 'r', encoding='utf-8') as f:
            result = f.read()
        
        self.assertEqual(result, expected_content)

    def test_no_trailing_empty_lines(self):
        content = "Line 1\nLine 2\nLine 3\n"
        expected_content = "Line 1\nLine 2\nLine 3\n"

        with open(self.file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        remove_trailing_empty_lines(self.file_path, 'utf-8')

        with open(self.file_path, 'r', encoding='utf-8') as f:
            result = f.read()
        
        self.assertEqual(result, expected_content)

    def test_all_lines_empty(self):
        content = "\n\n\n"
        expected_content = ""

        with open(self.file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        remove_trailing_empty_lines(self.file_path, 'utf-8')

        with open(self.file_path, 'r', encoding='utf-8') as f:
            result = f.read()
        
        self.assertEqual(result, expected_content)

    def test_mixed_empty_and_non_empty_lines(self):
        content = "\nLine 1\n\nLine 2\n\n"
        expected_content = "Line 1\nLine 2\n"

        with open(self.file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        remove_trailing_empty_lines(self.file_path, 'utf-8')

        with open(self.file_path, 'r', encoding='utf-8') as f:
            result = f.read()
        
        self.assertEqual(result, expected_content)


# class TestValidateTsvFile(unittest.TestCase):

#     def setUp(self):
#         self.valid_tsv_file = 'tests/valid_tsv.tsv'
#         self.invalid_empty_tsv_file = 'tests/invalid_empty_tsv.tsv'
#         self.invalid_format_tsv_file = 'tests/invalid_format_tsv.tsv'
#         self.invalid_column_count_tsv_file = 'tests/invalid_column_count_tsv.tsv'
        
#         # Create test files
#         with open(self.valid_tsv_file, 'w', encoding='utf-8') as f:
#             f.write('header1\theader2\theader3\n')
#             f.write('data1\tdata2\tdata3\n')
        
#         with open(self.invalid_empty_tsv_file, 'w', encoding='utf-8') as f:
#             f.write('')
        
#         with open(self.invalid_format_tsv_file, 'w', encoding='utf-8') as f:
#             f.write('header1\n')
        
#         with open(self.invalid_column_count_tsv_file, 'w', encoding='utf-8') as f:
#             f.write('header1\theader2\theader3\n')
#             f.write('data1\tdata2\n')

#     # def tearDown(self):
#     #     # Remove test files
#     #     for file_path in [
#     #         self.valid_tsv_file,
#     #         self.invalid_empty_tsv_file,
#     #         self.invalid_format_tsv_file,
#     #         self.invalid_column_count_tsv_file
#     #     ]:
#     #         if os.path.exists(file_path):
#     #             os.remove(file_path)

#     def test_valid_tsv_file(self):
#         headers = validate_tsv_file(self.valid_tsv_file, encoding='utf-8')
#         self.assertEqual(headers, ['header1', 'header2', 'header3'])

#     def test_empty_tsv_file(self):
#         with self.assertRaises(ValueError) as cm:
#             validate_tsv_file(self.invalid_empty_tsv_file, encoding='utf-8')
#         self.assertEqual(str(cm.exception), "TSV file is empty.")

#     def test_invalid_format_tsv_file(self):
#         with self.assertRaises(ValueError) as cm:
#             validate_tsv_file(self.invalid_format_tsv_file, encoding='utf-8')
#         self.assertEqual(str(cm.exception), "Invalid TSV format: Expected tab-separated headers.")

#     def test_invalid_column_count_tsv_file(self):
#         with self.assertRaises(ValueError) as cm:
#             validate_tsv_file(self.invalid_column_count_tsv_file, encoding='utf-8')
#         self.assertTrue(str(cm.exception).startswith("Line 2 does not match the number of columns in the header."))




class TestDiaghoCreateJsonFamilies(unittest.TestCase):

    def setUp(self):
        self.input_file = 'tests/test_output.json'
        self.output_file = 'tests/output.families.json'

    # def tearDown(self):
    #     # Clean up test files
    #     for file in [self.input_file, self.output_file]:
    #         if os.path.exists(file):
    #             os.remove(file)

    
    def test_diagho_create_json_families(self):
        
        self.assertEqual.__self__.maxDiff = None
        
        diagho_create_json_families(self.input_file, self.output_file)
        
        with open(self.output_file) as json_outputfile:
            result = json.load(json_outputfile)
        
        # Check
        expected_dict_families = {
            "families": [
                {
                    "identifier": "23-16947",
                    "persons": [
                        {
                            "identifier": "23-16947",
                            "sex": "male",
                            "firstName": "RE",
                            "lastName": "GE",
                            "birthday": "2014-06-22",
                            "note": "EXOME-41"
                        }
                    ]
                },
                {
                    "identifier": "23-22594",
                    "persons": [
                        {
                            "identifier": "23-22589",
                            "sex": "female",
                            "firstName": "KA",
                            "lastName": "CO",
                            "birthday": "1975-06-03",
                            "note": "EXOME-48"
                        },
                        {
                            "identifier": "23-22594",
                            "sex": "male",
                            "firstName": "SA",
                            "lastName": "CO",
                            "birthday": "2008-05-06",
                            "motherIdentifier": "23-22589",
                            "fatherIdentifier": "23-32539",
                            "note": "EXOME-48"
                        },
                        {
                            "identifier": "23-32539",
                            "sex": "male",
                            "firstName": "SA",
                            "lastName": "CO",
                            "birthday": "1979-05-31",
                            "note": "EXOME-48"
                        }
                    ]
                }
            ]
        }
        
        self.assertEqual(result, expected_dict_families)


class TestDiaghoCreateJsonFiles(unittest.TestCase):
    
    def setUp(self):
        self.input_file = 'tests/test_output.json'
        self.output_file = 'tests/output.files.json'

    def test_diagho_create_json_files(self):
        
        self.assertEqual.__self__.maxDiff = None

        # Run the function
        diagho_create_json_files(self.input_file, self.output_file, "/ngs/datagen/diagho/cytogen/dataset_selected_families/vcfs_annotated")

        with open(self.output_file) as json_outputfile:
            result = json.load(json_outputfile)

        # Check the correct structure was written to the output file
        expected_output = {
                "files": [
                    {
                        "filename": "VDG_23-16947-A-02-00_vep.vcf.gz",
                        "samples": [
                            {
                                "name": "23-16947-A-02-00",
                                "person": "23-16947"
                            }
                        ],
                        "checksum": "ed132e8bf3182fd9b01ae8fa3b5b3aab"
                    },
                    {
                        "filename": "VDG_23-22594_vep.vcf.gz",
                        "samples": [
                            {
                                "name": "23-22589-A-04-00",
                                "person": "23-22589"
                            },
                            {
                                "name": "23-22594-A-07-00",
                                "person": "23-22594"
                            },
                            {
                                "name": "23-32539-A-04-00",
                                "person": "23-32539"
                            }
                        ],
                        "checksum": "70957313694c24c09ed1d2d54f5f8051"
                    }
                ]
        }
        
        self.assertEqual(result, expected_output)


class TestDiaghoCreateJsonInterpretations(unittest.TestCase):

    def setUp(self):
        self.input_file = 'tests/test_output.json'
        self.output_file = 'tests/output.interpretations.json'

    def test_create_json_interpretations(self):
        
        self.assertEqual.__self__.maxDiff = None
        
        # Run the function
        vcf_directory = "/ngs/datagen/diagho/cytogen/dataset_selected_families/vcfs_annotated"
        diagho_create_json_interpretations(self.input_file, self.output_file, vcf_directory)

        with open(self.output_file) as json_outputfile:
            result = json.load(json_outputfile)

        # Check the correct structure was written to the output file        
        expected_output = {
            "interpretations": [
                {
                    "family": "23-16947",
                    "indexCase": "23-16947",
                    "project": "vdg",
                    "title": "23-16947 - EXOME-41",
                    "priority": "2",
                    "datas": [
                        {
                            "type": 0,
                            "samples": [
                                {
                                    "name": "23-16947-A-02-00",
                                    "isAffected": True,
                                    "checksum": "ed132e8bf3182fd9b01ae8fa3b5b3aab"
                                }
                            ]
                        }
                    ]
                },
                {
                    "family": "23-22594",
                    "project": "vdg",
                    "priority": "2",
                    "datas": [
                        {
                            "type": 0,
                            "samples": [
                                {
                                    "name": "23-22589-A-04-00",
                                    "isAffected": False,
                                    "checksum": "70957313694c24c09ed1d2d54f5f8051"
                                },
                                {
                                    "name": "23-22594-A-07-00",
                                    "isAffected": True,
                                    "checksum": "70957313694c24c09ed1d2d54f5f8051"
                                },
                                {
                                    "name": "23-32539-A-04-00",
                                    "isAffected": False,
                                    "checksum": "70957313694c24c09ed1d2d54f5f8051"
                                }
                            ]
                        }
                    ],
                    "indexCase": "23-22594",
                    "title": "23-22594 - EXOME-48"
                }
            ]
        }

        self.assertEqual(result, expected_output)



if __name__ == '__main__':
    # unittest.main()
    test_output_file = 'tests/TestsCases_results.txt'
    
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    with open(test_output_file, 'w') as f:
        f.write(current_time)
        # runner = unittest.TextTestRunner(stream=f, verbosity=2)
        # unittest.main(testRunner=runner, exit=False)
        runner = unittest.TextTestRunner(stream=f, verbosity=2)
        
        # test_name = "TestValidateTsvFile"
        # suite = unittest.TestLoader().loadTestsFromTestCase(TestValidateTsvFile)
        # f.write("\n\n")
        # f.write("=======================================================\n")
        # f.write("Tests Cases : " + test_name + "\n")
        # f.write("=======================================================\n\n")
        # runner.run(suite)
        
        test_name = "TestRemoveTrailingEmptyLines"
        suite = unittest.TestLoader().loadTestsFromTestCase(TestRemoveTrailingEmptyLines)
        f.write("\n\n")
        f.write("=======================================================\n")
        f.write("Tests Cases : " + test_name + "\n")
        f.write("=======================================================\n\n")
        runner.run(suite)
        
        test_name = "TestDiaghoTsv2Json"
        suite = unittest.TestLoader().loadTestsFromTestCase(TestDiaghoTsv2Json)
        f.write("\n\n")
        f.write("=======================================================\n")
        f.write("Tests Cases : " + test_name + "\n")
        f.write("=======================================================\n\n")
        runner.run(suite)
        
        test_name = "TestDiaghoCreateJsonFamilies"
        suite = unittest.TestLoader().loadTestsFromTestCase(TestDiaghoCreateJsonFamilies)
        f.write("\n\n")
        f.write("=======================================================\n")
        f.write("Tests Cases : " + test_name + "\n")
        f.write("=======================================================\n\n")
        runner.run(suite)
        
        test_name = "TestDiaghoCreateJsonFiles"
        suite = unittest.TestLoader().loadTestsFromTestCase(TestDiaghoCreateJsonFiles)
        f.write("\n\n")
        f.write("=======================================================\n")
        f.write("Tests Cases : " + test_name + "\n")
        f.write("=======================================================\n\n")
        runner.run(suite)
        
        test_name = "TestDiaghoCreateJsonInterpretations"
        suite = unittest.TestLoader().loadTestsFromTestCase(TestDiaghoCreateJsonInterpretations)
        f.write("\n\n")
        f.write("=======================================================\n")
        f.write("Tests Cases : " + test_name + "\n")
        f.write("=======================================================\n\n")
        runner.run(suite)
        
        print("test END")
        
        