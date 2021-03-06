from parampool.tree.SubTree import SubTree

class Tree:

    def __init__(self, root=None, root_name='root'):
        if root is None:
            self.root = SubTree(root_name)
        else:
            assert isinstance(root, SubTree)
            self.root = root
        self.locator = self.root

        # map integer tree level to name (main, sub, subsub, etc.)
        self.level_name = {0: 'sub tree'}
        for i in range(1, 6):
            self.level_name[i] = 'sub'*(i+1) + ' tree'

    def subtree(self, path, subtree=None):
        """
        Go to subtree with relative path `path`. Add `subtree` here,
        or create a new subtree node if no subtree `path` exists.
        """
        path = TreePath(path)
        try:
            self.change_subtree(path)
        except NonExistingSubtreeError:
            # This subtree was not found.
            # self.locator is now at a position where we can make
            # the subtree or add the given subtree.
            if subtree is None:
                # As mkdir name; cd name
                new_subtree = SubTree(path.basename(),
                                      parent=self.locator)
            else:
                if isinstance(subtree, Pool):
                    subtree = subtree.root  # extract subtree
                if not isinstance(subtree, tree.SubTree):
                    raise TypeError(
                        'subtree must be Pool or subpool/SubTree, not %s'
                        % type(subtree))
                new_subtree = subtree
            self.locator.add(new_subtree)
            self.locator = new_subtree

    def add_leaf(self, leaf):
        """Create a new leaf object at current location (subtree)."""
        # As creating file in current dir
        self.locator.add(leaf)

    def get_current_subtree(self):
        return self.locator  # SubTree object

    def change_subtree(self, path):
        """Move to path in tree."""
        # path has same syntax as file path to a directory
        original_location = self.locator
        if not isinstance(path, TreePath):
            path = TreePath(path)

        if path.absolute():
            self.locator = self.root

        for subtree_name in path.to_tuple():
            found = False
            if subtree_name == '..':
                if self.locator.parent is None:
                    raise OutOfTreeError(
                        'path %s walks out of the tree' % path)
                else:
                    self.locator = self.locator.parent
                    found = True
            else:
                for item in self.locator:
                    if isinstance(item, SubTree):
                        if item.name == subtree_name:
                            self.locator = item
                            found = True
                            break
        if not found:
            raise NonExistingSubtreeError(
                'change_subtree: path=%s was not found' % path)

    def traverse(
        self,
        callback_leaf=None,
        callback_subtree_start=None,
        callback_subtree_end=None,
        level=0,
        tree_path=None,   # list of parent subtree names
        subtree=None,     # subtree to invoke
        user_data=None,   # users data - for in-place manipulation
        verbose=False):   # True: write out the traversal
        """
        Traverse the tree, starting from subtree (the root if None).
        At the start of each SubTree object, callback_subtree_start is
        called, for each leaf, callback_leaf is called, and at the
        end of the SubTree object, callback_subtree_end is called.
        These callback functions take four arguments: tree_path
        (with the complete path to the current subtree),
        level (the depth in the tree), item (the SubTree or Leaf object),
        and user_data which is some mutable data structure provided by
        the user and that can be filled in callback functions.
        """
        if subtree is None:
            subtree = self.root
        if tree_path is None:
            tree_path = []

        for item in subtree:
            if verbose:
                print 'traverse: %s (%s)' % \
                      (item.name, item.__class__.__name__)
            if isinstance(item, SubTree):
                tree_path.append(item.name)

                if callable(callback_subtree_start):
                    callback_subtree_start(
                        tree_path, level, item, user_data)

                self.traverse(callback_leaf,
                              callback_subtree_start,
                              callback_subtree_end,
                              level+1,
                              tree_path,
                              item,
                              user_data,
                              verbose)

                if callable(callback_subtree_end):
                    callback_subtree_end(
                        tree_path, level, item, user_data)

                del tree_path[-1]
            else:  # assume leaf
                if callable(callback_leaf):
                    callback_leaf(
                        tree_path, level, item, user_data)

    def __str__(self):
        """
        Return pretty print of tree using
        names of subtrees and leaves with indentation
        visualizing the subtree level.
        """
        def leaf_printer(tree_path, level, leaf, outlines):
            indentation = '    '*level
            outlines.append('%s%s' % (indentation, leaf.name))

        def subtree_printer(tree_path, level, subtree, outlines):
            indentation = '    '*level
            outlines.append('%s%s "%s" (level=%d)' %
                            (indentation, self.level_name[level],
                             tree_path[-1], level))

        outlines = []   # list of strings (to be printed)
        self.traverse(
            callback_leaf=leaf_printer,
            callback_subtree_start=subtree_printer,
            user_data=outlines)
        return '\n'.join(outlines)


class NonExistingSubtreeError(Exception):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return self.message

    __repr__ = __str__

class OutOfTreeError(Exception):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return self.message

    __repr__ = __str__


class TreePath:
    """
    Representation of a tree path '/some/path/to/tree'.
    Internally, self.path holds ('some', 'path', 'to, 'leaf').
    """
    def __init__(self, path):
        """
        path can be ('some', 'path', 'to, 'leaf') or
        absolute path '/some/path/to/tree' or
        relative path '../../path/to/leaf'.
        """
        if isinstance(path, basestring):
            # /some/path/to/leaf
            self.path = path.split('/')
        elif isinstance(path, (list,tuple)):
            # ('some', 'path', 'to, 'leaf')
            self.path = list(path)

    def to_str(self):
        """Return string representation '/some/path/to/leaf'."""
        return '/' + '/'.join(self.path)

    def to_tuple(self):
        """Return tuple representation ('some', 'path', 'to, 'leaf')."""
        return self.path

    def parent(self):
        """Return parent path ("dirname" in a file system)."""
        return self.path[:-1]

    def basename(self):
        """Return stripped path (self.path[-1])."""
        return self.path[-1]

    def __getitem__(self, i):
        return self.path[i]

    def absolute(self):
        """Return True if absolute path."""
        return self.path[0] == ''

    def relative(self):
        """Return True if relative path."""
        return not self.absolute()

    def __str__(self):
        return self.to_str()

def get_all_tree_paths(tree, add_leaf_object=False):
    """Return list of all leaf names in the tree."""
    def leaf_path(tree_path, level, leaf, paths):
        path = '/' + '/'.join(tree_path) + '/' + leaf.name
        if add_leaf_object:
            paths.append((path, leaf))
        else:
            paths.append(path)

    paths = []
    tree.traverse(callback_leaf=leaf_path, user_data=paths)
    return paths

def hash_all_leaves(tree):
    """Return paths2leaves[path] = leaf_object."""
    paths = get_all_tree_paths(tree, add_leaf_object=True)
    paths2leaves = {path: leaf for path, leaf in paths}
    return paths2leaves

def unique_short_name(short_path, paths):
    """
    Check if `short_path` is a unique abbreviation of a full path.
    All full paths are stored in `path`.
    If unique match, return full path, otherwise return None.
    """
    short_paths = [path.split('/')[-1] for path in paths]
    n = short_paths.count(short_path)
    if n > 1:  # not unique
        return None
    elif n == 0:  # full path
        return short_path
    else: # unique match n=1
        index = short_paths.index(short_path)
        return paths[index]

def get_leaf(short_path, paths2leaves):
    """
    Return leaf object if `short_path` is a unique path name.
    `paths2leaves` is a dict with paths as keys and leaf
    objects as values.
    """
    path = unique_short_name(short_path, list(paths2leaves.keys()))
    if path is None:
        raise ValueError('%s is not a unique short name' % short_path)
    else:
        return paths2leaves[path]

# Is this one really necessary? Do not think so...
def get_subtree(short_path, paths2subtrees):
    # 2DO
    # Check if hash_all_leaves also creates paths to subtrees - no!
    return NotImplementedError

def dump(tree):
    """Dump tree using str() for subtrees and leaves."""
    def leaf_dump(tree_path, level, leaf, outlines):
        indentation = '    '*level
        outlines.append('%s%s' % (indentation, str(leaf)))

    def subtree_dump(tree_path, level, subtree, outlines):
        indentation = '    '*level
        outlines.append('%s%s "%s" (level=%d)' %
                        (indentation, tree.level_name[level],
                         tree_path[-1], level))

    outlines = []   # list of strings (to be printed)
    tree.traverse(
        callback_leaf=leaf_dump,
        callback_subtree_start=subtree_dump,
        user_data=outlines)
    return '\n'.join(outlines)

import nose.tools as nt
from parampool.utils import assert_equal_text

def test_Tree_basics():
    t = Tree(root_name='main')

    class Leaf:
        def __init__(self, name, default):
            self.name = name
            self.default = default

        def __str__(self):
            return '%s "%s"' % (self.__class__.__name__, self.name)

    t.add_leaf(Leaf(name='item1', default=1.0))
    nt.assert_equal(t.locator.name, 'main')
    nt.assert_equal(t.locator.tree[-1].name, 'item1')

    t.add_leaf(Leaf(name='item2', default=2.0))
    t.subtree('sub1')
    nt.assert_equal(t.locator.name, 'sub1')

    t.add_leaf(Leaf(name='item3', default=3))
    nt.assert_equal(t.locator.name, 'sub1')
    nt.assert_equal(t.locator.tree[-1].name, 'item3')

    t.subtree('../sub2')
    t.add_leaf(Leaf(name='item4', default=4))
    nt.assert_equal(t.locator.name, 'sub2')
    nt.assert_equal(t.locator.tree[-1].name, 'item4')
    nt.assert_equal(str(t.locator), '[Leaf "item4"]')
    nt.assert_equal(t.locator.get_parent().name, 'main')

    t.subtree('sub3')
    t.add_leaf(Leaf(name='item5', default=5))
    t.subtree('sub4')
    t.add_leaf(Leaf(name='item6', default=6))
    t.add_leaf(Leaf(name='item7', default=7))
    t.add_leaf(Leaf(name='item8', default=8))
    t.add_leaf(Leaf(name='item9', default=9))
    t.subtree('..')
    nt.assert_equal(t.locator.name, 'sub3')

    t.add_leaf(Leaf(name='item10', default=10))
    t.subtree('sub4')
    t.subtree('../../sub5')
    t.add_leaf(Leaf(name='item11', default=11))
    t.subtree('/sub2/sub3/sub4')
    t.add_leaf(Leaf(name='item12', default=12))
    reference = """\
item1
item2
sub tree "sub1" (level=0)
    item3
sub tree "sub2" (level=0)
    item4
    subsub tree "sub3" (level=1)
        item5
        subsubsub tree "sub4" (level=2)
            item6
            item7
            item8
            item9
            item12
        item10
    subsub tree "sub5" (level=1)
        item11"""
    assert_equal_text(str(t), reference)

    reference = '''\
Leaf "item1"
Leaf "item2"
sub tree "sub1" (level=0)
    Leaf "item3"
sub tree "sub2" (level=0)
    Leaf "item4"
    subsub tree "sub3" (level=1)
        Leaf "item5"
        subsubsub tree "sub4" (level=2)
            Leaf "item6"
            Leaf "item7"
            Leaf "item8"
            Leaf "item9"
            Leaf "item12"
        Leaf "item10"
    subsub tree "sub5" (level=1)
        Leaf "item11"'''
    assert_equal_text(dump(t), reference)

if __name__ == '__main__':
    test_Tree_basics()
