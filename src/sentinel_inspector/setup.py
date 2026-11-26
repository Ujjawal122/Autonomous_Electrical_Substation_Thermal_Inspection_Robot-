import os
from glob import glob
from setuptools import find_packages, setup

package_name = 'sentinel_inspector'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'),
            glob(os.path.join('launch', '*launch.[pxy][yma]*'))),
        (os.path.join('share', package_name, 'config'),
            glob(os.path.join('config', '*'))),
        (os.path.join('share', package_name, 'maps'),
            glob(os.path.join('maps', '*'))),
    ],
    package_data={'': ['py.typed']},
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='ujjaw',
    maintainer_email='ujjaw@todo.todo',
    description='TODO: Package description',
    license='TODO: License declaration',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
             'thermal_vision = sentinel_inspector.thermal_vision_node:main',
            'battery_monitor = sentinel_inspector.battery_monitor_node:main',
            'patrol_manager = sentinel_inspector.patrol_manager:main',
        ],
    },
)
