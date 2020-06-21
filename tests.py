import inspect
import unittest
import gdrive


#class FoldersTestCase(unittest.TestCase):
#
#    def setUp(self):
#        self.drive = gdrive.GoogleDrive()
#
#    def test_crud_folder(self):
#        ret = self.drive.create_folder('Foo')
#        self.assertTrue(ret)
#        
#        ret = self.drive.find_folder('Foo')
#        self.assertTrue(ret)
#
#        ret = self.drive.rename_folder('Foo', 'Bar')
#        self.assertTrue(ret)
#
#        ret = self.drive.find_folder('Bar')
#        self.assertTrue(ret)
#
#        ret = self.drive.delete_folder('Bar')
#        self.assertFalse(ret)

#if __name__ == "__main__":
#    test_src = inspect.getsource(Test)
#    unittest.TestLoader.sortTestMethodsUsing = lambda _, x, y: (
#        test_src.index(f"def {x}") - test_src.index(f"def {y}")
#    )
#    unittest.main(verbosity=2)
if __name__ == '__main__':
    drive = gdrive.GoogleDrive()
    ret = drive.create_folder('Foo', allow_duplicated=False)
    assert ret is not None

    ret = drive.create_folder('Foo', allow_duplicated=False)
    assert ret is None

    ret = drive.get_folder('Foo')
    assert ret.get('id') is not None

    ret = drive.delete_folder('Foo')
    assert ret is None

    # Listing things

    ret = drive.create_folder('Foo', allow_duplicated=False)
    assert ret is not None

    ret = drive.create_folder('Bar', parent='Foo', allow_duplicated=False)
    assert ret is not None

    ret = drive.get_folders(parents=['Foo'])
    assert len(ret) == 1

    ret = drive.delete_folder('Bar')
    assert ret is None

    ret = drive.delete_folder('Foo')
    assert ret is None

    ret = drive.get_folders()
    assert len(ret) > 0

    ret = drive.create_file('hello.txt', 'uploaded_hello.txt')
    assert ret is not None

    ret = drive.delete_file('uploaded_hello.txt')
    assert ret is None

    ret = drive.get_file('uploaded_hello.txt')
    assert ret is None

    foo2 = gdrive.Folder('Foo2')
    assert foo2.uid is None

    foo2.create()
    assert foo2.uid is not None

    foo2.delete()
    assert foo2.uid is None

    #ret = drive.get_folder('Foo')
    #assert isinstance(ret, dict), 'x_x'
