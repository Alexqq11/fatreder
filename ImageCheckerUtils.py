import struct
import Core
import Structures

class FilesAllocationChecker:
    def __init__(self, core):
        self._core  = core
        self._fat_table = core.fat_table
        self._fat_boot_sector = core.fat_boot_sector
        self.utils = core.file_system_utils
        self.low_utils = core.file_system_utils.low_level_utils

        pass
    def check_cycles_in_file(self):
        pass

    def check_cycles_in_file(self, data_cluster):
        destination_to_cycle_start, cycle_length = self.floyd(self._fat_table.get_next, data_cluster)
        self._fat_table.fix_cycle(data_cluster , destination_to_cycle_start + cycle_length - 1) #equal len  of list  useful chain clusters - 1

    def clean_fat_trash(self):
        pass

    def floyd(self, get_next, start_cluster):
        slow_pointer = get_next(start_cluster)
        fast_pointer = get_next(get_next(start_cluster))
        while slow_pointer != fast_pointer:
            slow_pointer = get_next(slow_pointer)
            fast_pointer = get_next(get_next(fast_pointer))
        destination_to_cycle_start = 0
        slow_pointer = start_cluster
        while slow_pointer != fast_pointer:
            slow_pointer = get_next(slow_pointer)
            fast_pointer = get_next(fast_pointer)
            destination_to_cycle_start += 1
        cycle_length = 1
        fast_pointer = get_next(slow_pointer)
        while slow_pointer != fast_pointer:
            fast_pointer = get_next(fast_pointer)
            cycle_length += 1
        return destination_to_cycle_start, cycle_length
    pass

