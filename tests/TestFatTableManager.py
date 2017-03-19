import os
import sys
import unittest

import Core
from  FatReaderExceptions import *

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             os.path.pardir))


class FatTableTests(unittest.TestCase):
    def test_parsing_functional(self):
        core = Core.Core()
        core.init("./test.img")

        with self.subTest("Correct clusters list length"):  # may_be check content
            file_clusters = core.fat_table.get_file_clusters_list(
                core.file_system_utils.working_directory.entries_list[5].data_cluster)
            length = len(file_clusters)
            # print("len", length)
            self.assertTrue(length == 9411)

        with self.subTest("Correct clusters list content"):
            file_clusters = core.fat_table.get_file_clusters_list(
                core.file_system_utils.working_directory.entries_list[5].data_cluster)
            f = open("./cluster_list_content_test")
            test_list = [int(line[0:-1]) for line in f]
            self.assertListEqual(file_clusters, test_list)
        with self.subTest("Correct free size"):
            size = core.fat_table.calculate_free_space()
            print(size)
            self.assertTrue(True)

    def test_allocation_functional(self):
        core = Core.Core()
        core.init("./test.img")
        fat_worker = core.fat_table

        with self.subTest("Incorrect allocation size"):
            with self.assertRaises(AllocationMemoryOutException):
                fat_worker.allocate_place(31300)

        allocate_number = 200
        empty_entry = fat_worker.allocate_place(allocate_number)

        with self.subTest("check_correct_allocation_status"):
            self.assertTrue(True)

        with self.subTest("check_correct_allocation_size"):
            lst = fat_worker.get_file_clusters_list(empty_entry)
            print(len(lst) , "   ", 200)
            self.assertTrue(len(lst) == allocate_number)

        with self.subTest("check_erase_allocation"):
            lst = fat_worker.get_file_clusters_list(empty_entry)
            fat_worker.delete_file_fat_chain(empty_entry)
            is_correct = True
            for entry in lst:
                addr = core.fat_table._main_fat._get_fat_entry_global_offset(entry)
                data = core.image_reader.get_data_global(addr, 4, True)
                is_correct = data == 0
                if not is_correct:
                    break
            self.assertTrue(is_correct)

    def test_correct_writes_functional(self):
        core = Core.Core()
        core.init("./test.img")
        file_clusters = core.fat_table.get_file_clusters_list(
            core.file_system_utils.working_directory.entries_list[5].data_cluster)
        working_cluster = file_clusters[len(file_clusters) - 1]

        core.fat_table.extend_file(working_cluster, 50)

        with self.subTest("check_extended_clusters_amount"):
            file_clusters2 = core.fat_table.get_file_clusters_list(
                core.file_system_utils.working_directory.entries_list[5].data_cluster)
            self.assertTrue(len(file_clusters) + 50 == len(file_clusters2))
        core.fat_table.delete_file_fat_chain(working_cluster, True)

        with self.subTest("check_deleted_clusters_amount"):
            file_clusters2 = core.fat_table.get_file_clusters_list(
                core.file_system_utils.working_directory.entries_list[5].data_cluster)
            self.assertTrue(len(file_clusters) == len(file_clusters2))

        with self.subTest("check_correct_file_state_after_operations"):
            file_clusters2 = core.fat_table.get_file_clusters_list(
                core.file_system_utils.working_directory.entries_list[5].data_cluster)
            self.assertListEqual(file_clusters, file_clusters2)

    def test_allocator_functional(self):
        core = Core.Core()
        core.init("./test.img")
        empty_entries = core.fat_table.find_empty_entries(50)

        with self.subTest("check_is_empty_fat_entries"):
            is_correct = True
            for entry in empty_entries:
                addr = core.fat_table._main_fat._get_fat_entry_global_offset(entry)
                data = core.image_reader.get_data_global(addr, 4, True)
                is_correct = data == 0
                if not is_correct:
                    break
            self.assertTrue(is_correct)
        with self.subTest("Check_empty_entries_amount"):
            self.assertTrue(len(empty_entries) == 50)

        with self.subTest("Check break allocation"):
            with self.assertRaises(AllocationMemoryOutException):
                cache = core.fat_table.find_empty_entries(31300)
            #self.assertFalse(cache[1])

        cache = core.fat_table.find_empty_entries(31000)

        with self.subTest("check iS empty fat entries big allocate"):
            is_correct = True
            for entry in cache:
                addr = core.fat_table._main_fat._get_fat_entry_global_offset(entry)
                data = core.image_reader.get_data_global(addr, 4, True)
                is_correct = data == 0
                if not is_correct:
                    break
            self.assertTrue(is_correct)

        with self.subTest("Check cant allocate"):
            with self.assertRaises(AllocationMemoryOutException):
                cache = core.fat_table.find_empty_entries(31225)
            #self.assertFalse(cache[1])  # TODO MAKE SIZE CHEKER FOR ALLOCATING DISK SPACE
