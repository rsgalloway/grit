#!/usr/bin/env python

import os
import sys
import time
import tempfile
import unittest

path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, path)
from grit import Repo, Item, Server

test_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'puppy.jpg')

class BasicTests(unittest.TestCase):

    def setUp(self):
        # create a new repo instance
        n = int(time.time())
        self.tempdir = os.path.join(tempfile.gettempdir(), 'grit-unittest-%d' % n)
        self.repo = Repo.new(self.tempdir)
        time.sleep(1)

    def tearDown(self):
        # cleanup
        self.repo.delete()

    def test_set_desc(self):
        # test setting the description
        desc = 'unit test for ' + self.repo.name
        self.repo.setDescription(desc)
        self.assertEqual(self.repo.getDescription(), desc)

    def test_add_version(self):
        # test adding a version
        n = len(self.repo.versions())
        v = self.repo.addVersion()
        v.save('add version test')
        self.assertEqual(len(self.repo.versions()), n+1)

    def test_add_item(self):
        # test adding an item
        self.assertEqual(len(self.repo.items()), 0)
        self.repo.addFile(test_file, 'adding test file')
        self.assertEqual(len(self.repo.items()), 1)

    def test_find_item(self):
        # test finding by name
        self.assertEqual(len(self.repo.items(os.path.basename(test_file))), 0)
        self.repo.addFile(test_file, 'adding test file')
        self.assertEqual(len(self.repo.items(os.path.basename(test_file))), 1)

    def test_remove_item(self):
        # test removing items from a version
        v = self.repo.addVersion()
        v.addFile(test_file)
        self.assertEqual(len(v.items()), 1)
        v.removeItem(v.items(os.path.basename(test_file))[0])
        self.assertEqual(len(v.items()), 0)
        v.save('removing puppy')
        self.assertEqual(len(self.repo.items()), 0)

    def test_new_branch(self):
        # test creating a new branch
        b = self.repo.branch('branch')
        self.assertEqual(b.parent.name, self.repo.name)
        self.assertEqual(len(b.items()), 0)
        self.repo.addFile(test_file, 'adding test file')
        self.assertEqual(len(b.items()), 1)

    def test_del_branch(self):
        # test deleting branches
        from grit import get_repos
        branches = get_repos(self.repo.path)
        for branch in branches:
            branch.delete()
        self.assertEqual(len(get_repos(self.repo.path)), 0)

if __name__ == '__main__':
    unittest.main()
