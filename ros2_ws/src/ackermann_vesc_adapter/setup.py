from setuptools import find_packages, setup

package_name = 'ackermann_vesc_adapter'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Alex Prediger',
    maintainer_email='alex.prediger@th-koeln.de',
    description='TODO: Package description',
    license='TODO: License declaration',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    
 entry_points={
    'console_scripts': [
        'ackermann_to_vesc = ackermann_vesc_adapter.ackermann_to_vesc:main',
    ],
    },
)
