import datetime
import os
import struct
import sys
import unittest

import Core
import FileEntryCreator
import FileEntryMetaData
import ImageWorker
import ReservedRegionReader

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             os.path.pardir))


class FatTablesReadersTests(unittest.TestCase):
    def test_file_entry_creator(self):
        creator = FileEntryCreator.FileEntryCreator()
        dir_listing = (b"NAME.NAM", b"NAME~1.NAM", b"NAME~2.NAM", b"NAME~3.NAM", b"NAME~4.NAM")
        control_time = datetime.datetime.now()
        name = "name.name_dir_epta_huepta_blyaa"
        entry_list = creator.new_entry(name, "a,h,r", 67, 45, dir_listing, control_time)
        with self.subTest("short_name"):
            self.assertTrue(entry_list[0][0:11] == b'NAME~5  NAM')
        with self.subTest("entries_amount"):
            self.assertTrue(((len(name) + 12) // 13 + 1) == len(entry_list))
        self.assertTrue(True)
        with self.subTest("check_name_split"):
            lst1 = creator.split_name("123456789012312345678901231234567890")
            lst2 = ("1234567890123", "1234567890123", "1234567890")
            self.assertTupleEqual(lst1, lst2)

    def test_file_file_entry_short_creator(self):
        short_creator = FileEntryCreator.ShortEntryCreator()
        with self.subTest("tests_for_generate_last_value"):
            short_creator = FileEntryCreator.ShortEntryCreator()
            with self.subTest("test_generate_last_value_file_exist"):
                short_creator.dir_listing = (
                b"AANAME~1.EXE", b"AANAME~2.EXE", b"AANAME~3.EXE", b"AANAME~4.EXE", b"AANAME~5.EXE")
                name = short_creator._generation_last_value(b"AANAME~1.EXE")
                self.assertTrue(name == b"AANAME~6.EXE")
            with self.subTest("test_generate_last_value_file_bad_parse_on, but not exist"):
                short_creator.dir_listing = (
                b"AANAME~1.EXE", b"AANAME~2.EXE", b"AANAME~3.EXE", b"AANAME~4.EXE", b"AANAME~5.EXE")
                name = short_creator._generation_last_value(b"NAME~1.EXE", True)
                self.assertTrue(name == b"NAME~1~1.EXE")
            with self.subTest("test_generate_last_value_file_name_too_long"):
                short_creator.dir_listing = (
                b"AANAME~1.EXE", b"AANAME~2.EXE", b"AANAME~3.EXE", b"AANAME~4.EXE", b"AANAME~5.EXE")
                name = short_creator._generation_last_value(b"AANAMEFUCKFUCK.EXE")
                self.assertTrue(name == b"AANAME~6.EXE")
            with self.subTest("test_generate_last_value_file_name_normal"):
                short_creator.dir_listing = (
                b"AANAME~1.EXE", b"AANAME~2.EXE", b"AANAME~3.EXE", b"AANAME~4.EXE", b"AANAME~5.EXE")
                name = short_creator._generation_last_value(b"AANAMEFF.EXE")
                self.assertTrue(name == b"AANAMEFF.EXE")
            self.assertTrue(True)

        with self.subTest("test_clear_name_content"):
            short_creator = FileEntryCreator.ShortEntryCreator()
            with self.subTest("name with space"):
                cleared, marker = short_creator._clear_name_content("  Folder  Name ")
                self.assertTrue(cleared == "FOLDERNAME" and marker == -1)
            with self.subTest("name with space"):
                cleared, marker = short_creator._clear_name_content("  .Folder. . .Name ")
                self.assertTrue(cleared == "FOLDER.NAME" and marker != -1)
            self.assertTrue(True)

        with self.subTest("test_translate_name_to_oem"):
            short_creator = FileEntryCreator.ShortEntryCreator()
            with self.subTest("normal_name_test"):
                oem_str, marker = short_creator._encode_name_to_oem_encoding("FOLDER.HUELDER")
                self.assertTrue(oem_str == b'FOLDER.HUELDER' and not marker)
            with self.subTest("name_with_bad_symbols_test"):
                oem_str, marker = short_creator._encode_name_to_oem_encoding("F=O+\L/D,E;R.H]U[ELDER")
                self.assertTrue(oem_str == b'F_O__L_D_E_R.H_U_ELDER' and marker)
            self.assertTrue(True)

        with self.subTest("test_translate_name_to_short_name"):
            short_creator = FileEntryCreator.ShortEntryCreator()
            with self.subTest("normal_name_test"):
                oem_str = short_creator._translate_to_short_name(b"FOLDER", -1)
                self.assertTrue(oem_str == b'FOLDER')
            with self.subTest("name_long_test"):
                oem_str = short_creator._translate_to_short_name(b"FOLDER_HUELDER", -1)
                self.assertTrue(oem_str == b'FOLDER_H')

            with self.subTest("name_short_with_long_extension"):
                oem_str = short_creator._translate_to_short_name(b"FOLD.ER_HUELDER", 4)
                self.assertTrue(oem_str == b'FOLD.ER_')
            with self.subTest("name_long_with_long_extension"):
                oem_str = short_creator._translate_to_short_name(b"FOLDER_HUE.LDER", 4)
                self.assertTrue(oem_str == b'FOLDER_H.LDE')
            with self.subTest("name_long_with_short_extension"):
                oem_str = short_creator._translate_to_short_name(b"FOLDER_HUE.L", 4)
                self.assertTrue(oem_str == b'FOLDER_H.L')
            with self.subTest("name_short_with_short_extension"):
                oem_str = short_creator._translate_to_short_name(b"FOLD.E", 4)
                self.assertTrue(oem_str == b'FOLD.E')
            self.assertTrue(True)
        with self.subTest("shortEntryCreator_test"):
            short_creator = FileEntryCreator.ShortEntryCreator()
            dir_listing = (b"NAME.NAM", b"NAME~1.NAM", b"NAME~2.NAM", b"NAME~3.NAM", b"NAME~4.NAM")
            control_time = datetime.datetime.now()
            oem_str = short_creator.new_entry("name.name_dir", "a,h,r", 67, 45, dir_listing, control_time)[0]
            with self.subTest("correct_name"):
                self.assertTrue(oem_str[0:11] == b'NAME~5  NAM')
            with self.subTest("correct_attr"):
                self.assertTrue(oem_str[11:12] == b'\x23')
            with self.subTest("correct_datetime"):
                time_bytes = oem_str[22:24]
                date_bytes = oem_str[24:26]
                time_parser = FileEntryMetaData.DateTimeFormat(struct.unpack('<H', date_bytes)[0],
                                                               struct.unpack('<H', time_bytes)[0])
                d1 = time_parser.datetime
                d2 = control_time
                self.assertTrue(d1.date() == d2.date()
                                and d1.hour == d2.hour
                                and d1.minute == d2.minute
                                and d1.second + 2 > d2.second
                                and d1.second - 2 < d2.second)

            with self.subTest("file_size"):
                size_bytes = oem_str[28:32]

                self.assertTrue(struct.unpack('<I', size_bytes)[0] == 45)

            with self.subTest("data_cluster"):
                self.assertTrue(struct.unpack('<I', oem_str[26:28] + oem_str[20:22])[0] == 67)
        self.assertTrue(True)

    def test_file_file_entry_long_creator(self):
        long_creator = FileEntryCreator.LongEntryCreator()
        entry1 = long_creator.new_entry("name", 1, 255, is_last=True)[0]
        with self.subTest("test_name_correct_length"):
            full_name = entry1[1:11] + entry1[14:26] + entry1[28:]
            self.assertTrue(len(full_name) == 26)
        with self.subTest("test_name_short_correct_translated"):
            full_name = entry1[1:11] + entry1[14:26] + entry1[28:32]
            full_name = full_name.decode("utf-16")
            full_name = full_name.strip('\0 ￿')
            self.assertTrue(full_name == "name")
        with self.subTest("test_correct_ldir_attribute"):
            self.assertTrue(entry1[11:12] == b'\x0f')
        with self.subTest("test_correct_ldir_check_sum"):
            self.assertTrue(entry1[13:14] == b'\xff')
        with self.subTest("test_correct_ldir_cluster_low"):
            self.assertTrue(entry1[26:28] == b'\x00\x00')
        with self.subTest("test_correct_ldir_type"):
            self.assertTrue(entry1[12:13] == b'\x00')
        with self.subTest("test_correct_ldir_number"):
            self.assertTrue(entry1[0:1] == b'\x41')

        entry2 = long_creator.new_entry("name_name_123", 4, 255, is_last=False)[0]

        with self.subTest("test_name_full_correct_translated"):
            full_name = entry2[1:11] + entry2[14:26] + entry2[28:32]
            full_name = full_name.decode("utf-16")
            self.assertTrue(full_name == "name_name_123")
        with self.subTest("test_correct_ldir_number"):
            self.assertTrue(entry2[0:1] == b'\x04')

    def test_time_parsers(self):
        control_time = datetime.datetime.now()
        time_converter = FileEntryMetaData.DateTimeGetter(control_time)
        time_bytes = time_converter.time_bytes
        date_bytes = time_converter.date_bytes
        time_parser = FileEntryMetaData.DateTimeFormat(struct.unpack('<H', date_bytes)[0],
                                                       struct.unpack('<H', time_bytes)[0])
        # print(control_time.isoformat(sep=':'),'  ', time_parser.datetime.isoformat(sep=':') )
        d1 = time_parser.datetime
        d2 = control_time
        self.assertTrue(d1.date() == d2.date()
                        and d1.hour == d2.hour
                        and d1.minute == d2.minute
                        and d1.second + 2 > d2.second
                        and d1.second - 2 < d2.second)

    def test_bpb_table_worker(self):
        reader = ImageWorker.ImageReader("./bpb_table")
        sector_parsed = ReservedRegionReader.BootSectorParser(reader)
        with self.subTest("correct_cluster_count_number"):
            self.assertTrue(sector_parsed.calc_cluster_number(sector_parsed.root_directory_offset) == 2)
        with self.subTest("correct_cluster_offset"):
            self.assertTrue(sector_parsed.calc_cluster_offset(2) == sector_parsed.root_directory_offset)
        with self.subTest("correct_fat_offsets"):
            self.assertTrue(
                sector_parsed.fat_offsets_list[0] == 3152896 and sector_parsed.fat_offsets_list[1] == 3673600)
        with self.subTest("correct_fat_zone_offset"):
            self.assertTrue(sector_parsed.fat_zone_offset == 3152896)
        with self.subTest("correct_cluster_size"):
            self.assertTrue(sector_parsed.cluster_size == 4096)
        with self.subTest("correct_fat_size"):
            self.assertTrue(3673600 - 3152896 == sector_parsed.fat_size)
        with self.subTest("correct_fat_size"):
            self.assertTrue(sector_parsed.root_directory_offset == 4194304)

    def test_parsing_functional(self):
        core = Core.Core()
        core.init("./test.img")
        with self.subTest("correct_clusters_list_length"):  # may_be check content
            file_clusters = core.fat_tripper.get_file_clusters_list(
                core.file_system_utils.working_directory.entries_list[5].data_cluster)
            self.assertTrue(len(file_clusters) == 9411)
        with self.subTest("correct_clusters_list_content"):
            file_clusters = core.fat_tripper.get_file_clusters_list(
                core.file_system_utils.working_directory.entries_list[5].data_cluster)
            f = open("./cluster_list_content_test")
            test_list = [int(line[0:-1]) for line in f]
            self.assertListEqual(file_clusters, test_list)

    def test_allocation_functional(self):
        core = Core.Core()
        core.init("./test.img")
        fat_worker = core.fat_tripper
        with self.subTest("incorrect_allocation_size"):
            empty_entry, status = fat_worker.allocate_place(31300)
            self.assertFalse(status and empty_entry == 0)
        allocate_number = 200
        empty_entry, status = fat_worker.allocate_place(allocate_number)
        with self.subTest("check_correct_allocation_status"):
            self.assertTrue(status)
        with self.subTest("check_correct_allocation_size"):
            lst = fat_worker.get_file_clusters_list(empty_entry)
            self.assertTrue(len(lst) == allocate_number)
        with self.subTest("check_erase_allocation"):
            lst = fat_worker.get_file_clusters_list(empty_entry)
            fat_worker.delete_file_fat_chain(empty_entry)
            is_correct = True
            for entry in lst:
                addr = core.fat_tripper._get_fat_entry_global_offset(entry)
                data = core.image_reader.get_data_global(addr, 4, True)
                is_correct = data == 0
                if not is_correct:
                    break
            self.assertTrue(is_correct)

    def test_correct_writes_functional(self):
        core = Core.Core()
        core.init("./test.img")
        file_clusters = core.fat_tripper.get_file_clusters_list(
            core.file_system_utils.working_directory.entries_list[5].data_cluster)
        working_cluster = file_clusters[len(file_clusters) - 1]
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
                data = core.image_reader.get_data_global(addr, 4, True)
                is_correct = data == 0
                if not is_correct:
                    break
            self.assertTrue(is_correct)
        with self.subTest("Check_empty_entries_amount"):
            self.assertTrue(len(empty_entries[0]) == 50)

        with self.subTest("Check_break_allocation"):
            cache = core.fat_tripper.find_empty_entries(31300)
            self.assertFalse(cache[1])

        cache = core.fat_tripper.find_empty_entries(31200)
        with self.subTest("check_is_empty_fat_entries_big_allocate"):
            is_correct = True
            for entry in cache[0]:
                addr = core.fat_tripper._get_fat_entry_global_offset(entry)
                data = core.image_reader.get_data_global(addr, 4, True)
                is_correct = data == 0
                if not is_correct:
                    break
            self.assertTrue(is_correct and cache[1])

        with self.subTest("Check_cant_allocate"):
            cache = core.fat_tripper.find_empty_entries(31225)
            self.assertFalse(cache[1])  # TODO MAKE SIZE CHEKER FOR ALLOCATING DISK SPACE


if __name__ == '__main__':
    unittest.main()
