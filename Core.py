import mmap
import os
import struct
""""reserved region class """
""" bs - boot sector"""
""""bpb bios parameter block """
class FatBootSector:
    def __init__(self):
        self.bs_jmp_boot = None #0 3
        self.bs_oem_name = None #3 8
        self.bpb_bytes_per_sector = None #11 2
        self.bpb_sectors_per_cluster = None #13 1
        self.bpb_reserved_region_sectors_count = None #14 2
        self.bpb_number_fats = None # 16 1
        self.bpb_root_entry_count = None #17 2 for fat32 it zero
        self.bpb_total_sectors_16 = None #19 2 old sixteen bits field in fat 32 must be zero
        self.bpb_media = None # 21 1 stand
        self.bpb_fat_size_16 = None # 22 2 amount fat sectors for one fat12/16 table in fat32 zero watch to fat 32
        self.bpb_sectors_per_track = None # 24 2 for interrupt 13 and accses to disks with geometry #old tech
        self.bpb_number_heads = None # 26 2 ammount of disk heads
        self.bpb_hidden_sectors = None # 28 4
        self.bpb_total_sectors_32 = None # 32 4 new 32 bit field sm old 16 bit field
        # there was can been fat12/16 fields but we starting write fat 32 fields
        self.bpb_fat_size_32 = None  # 36 4 amoun of sectors one fat
        self.bpb_ext_flags = None #40 2
        self.file_system_version = None #42 2
        self.bpb_root_cluster = None# 44 4
        self.bpb_file_system_information = None #48 2
        self.bpb_backup_boot_sector = None # 50 2
        self.bpb_reserved = None # 52 12
        self.driver_number = None # 64 1
        self.bs_reserved1 = None # 65 1
        self.boot_signature = None# 66 1
        self.bs_volume_id = None# 67 4
        self.bs_volume_label = None # 71 11
        self.bs_file_system_type = None #82 8

class ImageReader:
    def __init__(self):




        pass
    pass
pass

pass
pass