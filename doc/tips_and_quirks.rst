Tips and quirks
---------------

TRUE and FALSE in design constraint properties
==============================================
By default :code:`'TRUE'`, :code:`'true'`, :code:`'True'` are interpreted by YAML as boolean and then printed to the file as :code:`'True'` string.
In .xdc file we want :code:`'TRUE'` string so double qoutes :code:`"` are needed.
Not sure which EDA tools can handle correctly :code:`'True'` or :code:`'true'` strings, but Xilinx Vivado can't.
The same applies to the :code:`"FALSE"`.

.. code-block:: yaml

   _default_:
     set_property:
       IOSTANDARD: LVDS_33
       # Use "TRUE" or "FALSE" strings for boolean properties.
       DIFF_TERM: "TRUE"

Net names on schematics
=======================
It is always preferred to put numbers at the end of net names in the board schematics files.
This is because in case of HDL, the array indexes are always at the end.
For example, following declaration:

.. code-block:: yaml

   _default_:
     regex:

   foo_[pn]_\[[0-4]\]:
     end: bar_[0-4]_[pn]

leads to improper assignment as order in natural sorting is different than what user expects.
This is because :code:`[0-4]` is before :code:`[pn]` in  :code:`bar_[0-4]_[pn]`.

Instead user needs to write it in a much more verbose way:

.. code-block:: yaml

   _default_:
     regex:

   foo_[pn]_\[0\]:
     end: bar_0_[pn]

   foo_[pn]_\[1\]:
     end: bar_1_[pn]

   foo_[pn]_\[2\]:
     end: bar_2_[pn]

   foo_[pn]_\[3\]:
     end: bar_3_[pn]

   foo_[pn]_\[4\]:
     end: bar_4_[pn]

Such verbosity could be avoided if the nets on the schematic were named in the following way :code:`bar_[pn]_[0-4]` instead of :code:`bar_[0-4]_[pn]`. Then following declaration

.. code-block:: yaml

   _default_:
     regex:

   foo_[pn]_\[[0-4]\]:
     end: bar_[pn]_[0-4]

would work as user expects.
