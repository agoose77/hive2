from setuptools import setup

setup(name='HIVE',
      version=0.1,
      description='Hive Nodal Logic',
      author='Sjoerd De Vries & Angus Hollands',
      author_email='goosey15+hive@gmail.com',
      url='https://github.com/agoose77/hive2',
      packages=['aphid', 'dragonfly', 'hive', 'hive_editor', 'testing', 'sparta'],
      include_package_data=True,
      scripts=['run_qt_gui.py'],

      # Project uses reStructuredText, so ensure that the docutils get
      # installed or upgraded on the target machine
      install_requires=['PyQt5', 'pygments', 'qdarkstyle'],
      )
