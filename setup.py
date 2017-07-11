from setuptools import setup

setup(name='hive2',
      version=0.1,
      description='Hive Nodal Logic',
      author='Sjoerd De Vries & Angus Hollands',
      author_email='goosey15+hive2@gmail.com',
      url='https://github.com/agoose77/hive2',
      packages=['aphid', 'dragonfly', 'hive', 'testing', 'sparta'],
      include_package_data=True,
      install_requires=['py_cfg_parsing']
)
