Mistakes detection
------------------

Safety and support in finding mistakes were among the core goals of the implementation.
The idea of the program is to report mistakes as soon as possible and exit with verbose mistake description.
It does not gather mistakes to report them all at the end, but reports them immediately at a given check point.
The application is capable of detecting and reporting the following mistakes:

#. Unassigned terminal pins - terminal pins not assigned to any ports.
#. Dangling terminal pins - terminal pins not mapped to any FPGA pins.
#. Assigning to non-terminal pins.
#. Conflicting mappings in each tree node. It detects such conflicts even if a given tree node is defined in multiple files.
#. Conflicting assignments - the same port assigned twice.
#. Assigning to missing pins.
#. Mapping to terminal pins.
