Overview
--------

FP2P (FPGA Port To Pin) is a tool for robust port to pin assignment in multi-board FPGA designs.
:numref:`fig_example_multiboard_fpga_design` shows an example of a multi-board FPGA design.

.. figure:: images/example_multiboard_fpga_design.jpg
   :name: fig_example_multiboard_fpga_design
   :alt: Example of a multi-board FPGA design.
   :align: center
   :scale: 40

   Example of a multi-board FPGA design.
   This setup is a development setup and needs assignment for 42 differential signals.
   The final design needs assignment for 210 differential signals.

The problem has been known for a long time and is especially annoying in data acquisition systems, where hundreds of signals are routed via multiple boards.
However, there is still no generic user-friendly open-source solution (or at least none has been found).
The implementation has two main goals, safety (check as many potential human mistakes as possible) and reusability (reuse connections mappings, defined in files, in multiple designs).
It is fully declarative and programming language-agnostic from the users perspective.
Currently 2 target EDA tools are supported Vivado and Quartus.
Adding support for another target EDA tool is very easy, as the analysis and resolving are completely decoupled from the constraint file generation.

If you want to jump straight to the examples check `example <https://github.com/m-kru/fp2p/tree/master/example>`_ and `tests <https://github.com/m-kru/fp2p/tree/master/tests>`_.

Status
======

The project is considered as finished.
Only bug fixes and minor improvements not breaking backward compatibility will be accepted.

License
=======

The project is licensed under the GPL-2.0 License.

Citation
========

If you find fp2p useful, and write any academic publication on a project utilizing fp2p please consider citing.

.. code-block:: md

   @ARTICLE{mkru_fp2p_ieee,
     author={Kruszewski, Michał and Zabołotny, Wojciech Marek},
     journal={IEEE Transactions on Nuclear Science},
     title={Safe and Reusable Approach for Pin-to-Port Assignment in Multiboard FPGA Data Acquisition and Control Designs},
     year={2021},
     volume={68},
     number={6},
     pages={1186-1193},
     doi={10.1109/TNS.2021.3074530}
   }
