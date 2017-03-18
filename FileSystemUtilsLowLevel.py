import posixpath

import DirectoryDescriptor
import FileReader


class PathObject:
    def __init__(self, exist, directory, raw_path, raw_desc, canonical_path, head_file_descriptor,
                 tail_file_descriptor):
        self._exist = exist
        self._directory = directory and exist
        self._raw_path = raw_path
        raw_parent, _ = posixpath.split(self._raw_path)
        self.raw_parent = raw_parent
        self._raw_path_descriptor = raw_desc
        self._canonical_path = canonical_path
        self._file = not directory and exist
        self._parent_exist = head_file_descriptor is not None
        head, tail = posixpath.split(posixpath.normpath(canonical_path)) if canonical_path else (None, None)
        self._tail = tail
        self._head = head
        self._root = head == '/' and tail == ''
        self._head_descriptor = head_file_descriptor
        self._tail_descriptor = tail_file_descriptor
        pass

    @property
    def file_fs_descriptor(self):
        if self.is_file:
            return self._tail_descriptor
        elif self.is_directory:
            return self._head_descriptor.find(self._tail, "by_name")

    @property
    def is_exist(self):
        return self._exist

    @property
    def is_directory(self):
        return self._directory

    @property
    def is_file(self):
        return self._file

    @property
    def parent_descriptor(self):
        return self._head_descriptor

    @property
    def path_descriptor(self):
        return self._tail_descriptor

    @property
    def file_directory_path(self):
        return self._head

    @property
    def file_name(self):
        return self._tail

    @property
    def is_root(self):
        return self._root

    @property
    def path(self):
        return self._canonical_path

    @property
    def raw_path(self):
        return self._raw_path

    @property
    def parent_exist(self):
        return self._parent_exist

    @property
    def raw_path_start_directory(self):
        """
        in case raw_way = canonical will be returned last file descriptor
        you can make comand back forward
        """
        return self._raw_path_descriptor


class FileSystemUtilsLowLevel:
    def __init__(self, core):
        self.core = core
        self.directory_reader = FileReader.DirectoryParser()
        self.directory_reader.init_core(core)
        # self.file_writer = FileWriter.FileWriter(core)

    def calc_cluster_offset(self, cluster_number):
        return self.core.fat_boot_sector.calc_cluster_offset(cluster_number)

    def parse_directory_descriptor(self, data_cluster):
        return self.directory_reader.parse_at_cluster(data_cluster)

    def get_directory_descriptor(self, path, working_directory):
        path = posixpath.normpath(path)
        if path == '/':
            return self.parse_directory_descriptor(self.core.fat_boot_sector.root_directory_cluster), True, 0
        path_parts = path.split('/')
        intermediate_directory = None
        operation_status = True
        track_num = 0
        for num, way_elem in enumerate(path_parts):
            track_num = num
            if way_elem == '' and intermediate_directory is None:
                intermediate_directory = self.parse_directory_descriptor(self.core.fat_boot_sector.root_directory_cluster)
            elif not (way_elem == '.' or (way_elem == '..' and (
                    intermediate_directory.is_root if intermediate_directory else working_directory.is_root))):
                if intermediate_directory is None:
                    intermediate_directory = working_directory
                dir_entry = intermediate_directory.find(way_elem, 'by_name_dir')
                if dir_entry:
                    intermediate_directory = self.parse_directory_descriptor(dir_entry.data_cluster)
                else:
                    operation_status = False
                    break
            elif intermediate_directory is None:
                intermediate_directory = working_directory
        return intermediate_directory, operation_status, track_num

    def get_canonical_path(self, directory_descriptor: DirectoryDescriptor.DirectoryDescriptor):
        parent_cluster = directory_descriptor.parent_directory_cluster
        own_cluster = directory_descriptor.data_cluster
        temp_dir = directory_descriptor
        name_stack = []
        while not temp_dir.is_root:
            temp_dir = self.parse_directory_descriptor(parent_cluster)
            fs = temp_dir.find(own_cluster, 'by_address')
            name_stack.append(fs.name)
            own_cluster = parent_cluster
            parent_cluster = temp_dir.parent_directory_cluster
        path = posixpath.join("/", *reversed(name_stack))
        return posixpath.normpath(path)

    def path_parser(self, path, working_directory):
        path = posixpath.normpath(path)
        directory, directory_exist, _ = self.get_directory_descriptor(path, working_directory)
        # directory_exist = None
        canonical_path = None
        path_exist = False
        tail_file_descriptor = None
        head_file_descriptor = None
        if directory_exist:
            canonical_path = self.get_canonical_path(directory)
            path_exist = True
            tail_file_descriptor = directory
            head, tail = posixpath.split(canonical_path)
            head_file_descriptor, _, _ = self.get_directory_descriptor(head, self.parse_directory_descriptor(self.core.fat_boot_sector.root_directory_cluster))
        else:
            head, tail = posixpath.split(path)
            directory, parent_directory_exist, _ = self.get_directory_descriptor(head, working_directory)
            if parent_directory_exist:
                canonical_path = posixpath.normpath(posixpath.join(self.get_canonical_path(directory), tail))
                tail_file_descriptor = directory.find(tail, "by_name")
                path_exist = tail_file_descriptor is not None
                head_file_descriptor = directory
        return PathObject(path_exist, directory_exist, path, working_directory,
                          canonical_path, head_file_descriptor, tail_file_descriptor)
