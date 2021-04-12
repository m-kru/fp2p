Special attributes
------------------

Special attributes are optional keys, that ease the work and reduce verbosity.

_default_
=========

Both mapping and assignment file types have one reserved key :code:`_default_` .
All information, set within value of the default key, is automatically applied to all remaining items in the file.
Setting the same option within given entry overwrites the default option.
In other words, everything defined within given entry has higher precedence than what is copied from the default.
Anything can be placed in the default section.
If it has no meaning, it will be simply ignored.

In case of the assignment file, there can be single *_default_* section per file and single *_default_* section per node.
Valuse set in the per node section take precedence.
Values set within the *_default_* sections can always be overwritten within the particular items.

.. code-block:: yaml
   :caption: :code:`_default_` attribute example.

   _default_:
     set_property:
       IOSTANDARD: LVDS_33
       DIFF_TERM: "TRUE"
     prefix: foo_
     suffix: _suffix

   board_1:
     _default_:
       prefix: prefix_

     A:
       end: pin_A
     B:
       end: pin_B
       set_property:
         DIFF_TERM: "FALSE"
       prefix: ""
     C:
       end: pin_C
       set_property:
         IOSTANDARD: LVDS_25
       suffix: ""

terminal
========

The :code:`terminal` key functions like a type annotation.
By default end pins are not intended to be connected to the FPGA ports.
To indicate, that the end pin must be connected to the port, a special property called terminal must be added to this end pin.
What is more, nothing more can be mapped to the pin marked as terminal.
To some extent, this mechanism is similar in its nature to the mutability aspect of the Rust programming language and provides the basics for extensive mistakes detection.
Terminal pins can be defined in each node of the tree, they are *not* limited only to the leaf nodes.

regex
=====

The :code:`regex` key is used to reduce verbosity.
It enables regex expanding (`sre_yield <https://github.com/google/sre_yield>`_) for the given mapping.
After expansion, natural (human) sorting (`natsort <https://github.com/SethMMorton/ natsort>`_) is applied to both names so that they can be mapped in a deterministic way.
In case of any mismatch of the lengths of generated lists the error is immediately reported.

.. code-block:: yaml
   :caption: :code:`regex` attribute example.

   A[1-3]:
     end: s[1-3]
     regex:
   # Above is equivalent to the following:
   A1:
     end: s1
   A2:
     end: s2
   A3:
     end: s3

prefix
======

If :code:`prefix` is set, its value is prepended to the name of each *key* denoting port name or pin name.

.. code-block:: yaml
   :caption: :code:`prefix` attribute example in a mapping file.

   _default_:
     prefix: foo_
   A1:
     end: s1
   A2:
     end: s2
   # Above is equivalent to the following:
   foo_A1:
     end: s1
   foo_A2:
     end: s2

suffix
======

If :code:`suffix` is set, its value is appended to the name of each *key* denoting port name or pin name.

end_prefix
==========

Same as :code:`prefix`, but applied to the value under the :code:`end` key.
Not yet implemented as there was no need for it so far.

end_suffix
==========

Same as :code:`suffix`, but applied to the value under the :code:`end` key.
Not yet implemented as there was no need for it so far.

set_property
============
The :code:`set_property` section is used for setting FPGA pin properties.
This attribute makes sense only for the assignment file and Vivado EDA tool.
When setting property, *key* is the name of the property and *value* is the value of the property.
See also :ref:`TRUE and FALSE in design constraint properties`, as it may save you some time.

Properties are not checked by the fp2p tool in any way.
They are simply forwarded to the auto generated constraint file, and later checked by the EDA tool.

set_instance_assignment
=======================
The :code:`set_instance_assignment` section is used for setting FPGA pin properties.
This attribute makes sense only for the assignment file and Quartus EDA tool.
