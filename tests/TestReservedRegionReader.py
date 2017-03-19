import os
import sys
import unittest

import ImageWorker
import ReservedRegionReader

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             os.path.pardir))


class ReservedRegionTests(unittest.TestCase):
    def test_bpb_table_worker(self):
        reader = ImageWorker.ImageReader("./bpb_table")
        sector_parsed = ReservedRegionReader.BootSectorParser(reader.get_data_global(0, 100))

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
