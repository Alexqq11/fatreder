import sys
import unittest
import os
import ImageWorker
import ReservedRegionReader
import FatTableReader
import Core
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             os.path.pardir))

class FatTablesReadersTests(unittest.TestCase):
    def test_bpb_table_worker(self):
        reader = ImageWorker.ImageReader("./bpb_table")
        sector_parsed = ReservedRegionReader.BootSectorParser(reader)
        with self.subTest("correct_cluster_count_number"):
            self.assertTrue(sector_parsed.calc_cluster_number(sector_parsed.root_directory_offset) == 2)
        with self.subTest("correct_cluster_offset"):
            self.assertTrue(sector_parsed.calc_cluster_offset(2) == sector_parsed.root_directory_offset)
        with self.subTest("correct_fat_offsets"):
            self.assertTrue(sector_parsed.fat_offsets_list[0] == 3152896 and sector_parsed.fat_offsets_list[1] == 3673600)
        with self.subTest("correct_fat_zone_offset"):
            self.assertTrue( sector_parsed.fat_zone_offset == 3152896)
        with self.subTest("correct_cluster_size"):
            self.assertTrue( sector_parsed.cluster_size == 4096)
        with self.subTest("correct_fat_size"):
            self.assertTrue(3673600 - 3152896 == sector_parsed.fat_size)
        with self.subTest("correct_fat_size"):
            self.assertTrue(sector_parsed.root_directory_offset == 4194304)
    def test_parsing_functional(self):
        core = Core.Core()
        core.init("./test.img")
        with self.subTest("correct_clusters_list_length"): # may_be check content
            file_clusters = core.fat_tripper.get_file_clusters_list(
                core.file_system_utils.working_directory.entries_list[5].data_cluster)
            self.assertTrue(len(file_clusters) == 9411)
        with self.subTest("correct_clusters_list_content"):
            file_clusters = core.fat_tripper.get_file_clusters_list(
                core.file_system_utils.working_directory.entries_list[5].data_cluster)
            f = open("./cluster_list_content_test")
            test_list = [int(line[0:-1]) for line in f]
            self.assertListEqual(file_clusters, test_list)
    def test_correct_writes_functional(self):
        core = Core.Core()
        core.init("./test.img")
        file_clusters = core.fat_tripper.get_file_clusters_list(
            core.file_system_utils.working_directory.entries_list[5].data_cluster)
        working_cluster = file_clusters[len(file_clusters) -1]
        core.fat_tripper.extend_file(working_cluster, 50)
        with self.subTest("check_extended_clusters_amount"):
            file_clusters2 = core.fat_tripper.get_file_clusters_list(
                core.file_system_utils.working_directory.entries_list[5].data_cluster)
            self.assertTrue(len(file_clusters) + 50 == len(file_clusters2))
        core.fat_tripper.delete_file_fat_chain(working_cluster, True)
        with self.subTest("check_deleted_clusters_amount"):
            file_clusters2 = core.fat_tripper.get_file_clusters_list(
                core.file_system_utils.working_directory.entries_list[5].data_cluster)
            self.assertTrue(len(file_clusters) == len(file_clusters2))
        with self.subTest("check_correct_file_state_after_operations"):
            file_clusters2 = core.fat_tripper.get_file_clusters_list(
                core.file_system_utils.working_directory.entries_list[5].data_cluster)
            self.assertListEqual(file_clusters, file_clusters2)

    def test_allocator_functional(self):
        core = Core.Core()
        core.init("./test.img")
        empty_entries = core.fat_tripper.find_empty_entries(50)
        with self.subTest("check_is_empty_fat_entries"):
            is_correct = True
            for entry in empty_entries[0]:
                addr = core.fat_tripper._get_fat_entry_global_offset(entry)
                data = core.image_reader.get_data_global(addr,4,True)
                is_correct = data == 0
                if not is_correct:
                    break
            self.assertTrue(is_correct)
        with self.subTest("Check_empty_entries_amount"):
            self.assertTrue(len(empty_entries[0]) == 50)

        cache = core.fat_tripper.find_empty_entries(31225)
        with self.subTest("check_is_empty_fat_entries_big_allocate"):
            is_correct = True
            for entry in cache[0]:
                addr = core.fat_tripper._get_fat_entry_global_offset(entry)
                data = core.image_reader.get_data_global(addr,4,True)
                is_correct = data == 0
                if not is_correct:
                    break
            self.assertTrue(is_correct)

        with self.subTest("Check_cant_allocate"):
            cache = core.fat_tripper.find_empty_entries(31225)
            self.assertFalse(cache[1]) # TODO MAKE SIZE CHEKER FOR ALLOCATING DISK SPACE

if __name__ == '__main__':
    unittest.main()