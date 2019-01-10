import datetime
import os
import struct
import sys
import unittest
from io import StringIO
from unittest.mock import patch
import sys


import Core
import FileEntryMetaData

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             os.path.pardir))
def print1(val, name):
    with open(name, "wt") as ff:
        ff.write(val)



class TestFatReaderAPP(unittest.TestCase):
    def test_global(self):
        core_ = Core.Core()
        core_.load('./test_4.img')
        core = core_.file_system_utils

        with self.subTest("ls command execute"):
            lst = list(core.ls('./'))
            self.assertListEqual(lst, ['/\nНОВЫЙ ТО.М\nSystem Volume Information\nматематика\n50\nзм 2013г\nКалинин А.Ю., Терешин Д.А. - Стереометрия 10.djvu\nКормен Т.,  Лейзерсон Ч., Ривест Р., Штайн K. - Алгоритмы. построение и анализ - 2005.djvu\nКормен, Лейзерсон, Ривест - Алгоритмы, построение, анализ.pdf'])


        with self.subTest("cd command execute"):
            core.cd('50')
            lst = list(core.ls('./'))
            self.assertListEqual(lst, ['/50\n.\n..\ndzheyms_erika_na_pyatdesyat_ottenkov_temnee.rtf.zip'])
            core.cd('.././математика/')

        with self.subTest("size command execute"):
            size = core.size('онуфриеночка.pdf')
            check = "873984"
            self.assertTrue(str(size) == check)

        with self.subTest("pwd command execute"):
                value = core.pwd()
                check = "/математика"
                self.assertTrue(value == check)

        with self.subTest("md short command execute"):
            core.md('test_folder')
            lst = list(core.ls('./'))
            self.assertListEqual(lst, ['/математика\n.\n..\nAlgebra_Shporka_k_aypodu_2_1.rtf\nзадачи оп планиметрии прасолов.pdf\nонуфриеночка.pdf\nзм 2013г\nНовая папка\ntest_folder'])

        with self.subTest("md long path command_execute"):
            core.cd("./test_folder/")
            core.md("./test_folder1/test_folder2/test_folder3/")
            core.cd("./test_folder1/test_folder2/test_folder3/")
            value = core.pwd()
            check = "/математика/test_folder/test_folder1/test_folder2/test_folder3"
            self.assertTrue(value == check)

        with self.subTest("cp command execute"):
            core.cp('/математика/зм 2013г/стереометрия.pdf', "./")
            core.cp('/математика/зм 2013г/стереометрия.pdf', "./")
            core.cp_export('./стереометрия(1).pdf', "./")
            core.cp_export('./стереометрия(1).pdf', "./")
            self.assertTrue(os.path.exists('./стереометрия(1).pdf'))
            self.assertTrue(os.path.exists('./стереометрия(2).pdf'))
            core.cp_import('./стереометрия(1).pdf', "./")
            core.cp_import('./стереометрия(2).pdf', "./")
            lst = list(core.ls('./'))
            self.assertListEqual(lst, ['/математика/test_folder/test_folder1/test_folder2/test_folder3\n.\n..\nстереометрия.pdf\nстереометрия(1).pdf\nстереометрия(2).pdf\nстереометрия(3).pdf'])
            os.remove('./стереометрия(1).pdf')
            os.remove('./стереометрия(2).pdf')

        with self.subTest("rename command execute"):
            core.rename('./стереометрия(3).pdf', 'st.pdf')
            core.rename('./стереометрия(2).pdf', 'sz123456789s1234.pdf')
            lst = list(core.ls('./'))
            self.assertListEqual(lst, ['/математика/test_folder/test_folder1/test_folder2/test_folder3\n.\n..\nстереометрия.pdf\nстереометрия(1).pdf\nsz123456789s1234.pdf\nst.pdf'])

        with self.subTest("move command execute"):
            core.move('./sz123456789s1234.pdf', '../')
            lst = list(core.ls('../'))
            self.assertListEqual(lst, ['/математика/test_folder/test_folder1/test_folder2\n.\n..\ntest_folder3\nsz123456789s1234.pdf'])

        with self.subTest("rm command execute"):
            core.rm('../sz123456789s1234.pdf')

        with self.subTest("rmdir command execute"):
            """kind of problems  move dir under current
             or remove under current is correct or not ? and may be we need memory test when delete files before and after"""
            core.cd('../')
            #core.rm('./sz123456789s1234.pdf')
            core.rmdir('./test_folder3')
            lst = list(core.ls('./'))
            self.assertListEqual(lst, ['/математика/test_folder/test_folder1/test_folder2\n.\n..'])
            core.cd('../../../../../../математика')
            core.rmdir('./test_folder')
            lst = list(core.ls('./'))
            self.assertListEqual(lst, ['/математика\n.\n..\nAlgebra_Shporka_k_aypodu_2_1.rtf\nзадачи оп планиметрии прасолов.pdf\nонуфриеночка.pdf\nзм 2013г\nНовая папка'])

        with self.subTest("cat commnd execute"):
            for x in core.cat('./онуфриеночка.pdf'):
                self.assertTrue(x)

        with self.subTest("cp folders copy execute"):
            core.md('test_folder1/test_folder2')
            core.cp('зм 2013г/стереометрия.pdf', "./test_folder1/test_folder2")
            core.cp_export('test_folder1', './')
            self.assertTrue(os.path.exists('./test_folder1/test_folder2'))
            self.assertTrue(os.path.exists('./test_folder1/test_folder2/стереометрия.pdf'))
            core.rmdir('test_folder1')
            core.cp_import('test_folder1', './')
            os.remove('./test_folder1/test_folder2/стереометрия.pdf')
            os.rmdir('test_folder1/test_folder2')
            os.rmdir('test_folder1')
            lst = list(core.ls('./', recursive=True))
            self.assertListEqual(lst,['/математика\n.\n..\nAlgebra_Shporka_k_aypodu_2_1.rtf\nзадачи оп планиметрии прасолов.pdf\nонуфриеночка.pdf\nзм 2013г\nНовая папка\ntest_folder1', '/математика/зм 2013г\n.\n..\nRasin_Deystvitelnye_chisla.pdf\nкомплексные числа.pdf\nмногочлены.pdf\nрасинка по алгебре.pdf\nрасинка по геометрии.pdf\nстереометрия.pdf\nзм 2013г', '/математика/зм 2013г/зм 2013г\n.\n..\nEX_11_13.PDF\nRasin_Deystvitelnye_chisla.pdf\nкомплексные числа.pdf\nмногочлены.pdf\nрасинка по алгебре.pdf\nрасинка по геометрии.pdf\nстереометрия.pdf', '/математика/Новая папка\n.\n..\n1.PNG\n2.PNG\n3.PNG\n4.PNG\n5.PNG\n6.PNG\n7.PNG\n8.PNG\n9vDL229Nfxc.jpg\nRotation of 9vDL229Nfxc.jpg', '/математика/test_folder1\n.\n..\ntest_folder2', '/математика/test_folder1/test_folder2\n.\n..\nстереометрия.pdf'])
            core.rmdir('test_folder1')

        with self.subTest("argpaser test"):
            import ArgparseModule
            argp = ArgparseModule.ArgsParser()
            self.assertTrue(argp is not None)







