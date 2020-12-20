File types
----------

The whole fp2p concept is based on 3 files types:

#. *mapping file* - one or more per setup,
#. *tree file* - one per setup,
#. *assignment file* - one per setup.

These three types share the same format and syntax, however their semantics is different.
`YAML <https://yaml.org/>`_ has been chosen as the file format.
Another user-friendly alternative was `JSON <https://www.json.org/json-en.html>`_, which is provided in the Python Standard Library.
However, YAML has been chosen as it is less verbose and allows placing comments in the files, what might be useful in case of documenting any peculiarities in the mappings.


Mapping file
============

The mapping file is used for defining physical connections between pins within the board, cables or connectors.

.. code-block:: yaml
   :caption: Example mapping file.

   A[1-3]:
     end: s[1-3]
     regex:
   A4:
     end: end_pin_4
     terminal:
   B1[2-3]:
     end: s_diff_pin_[pn]
     regex:

The mapping file is a dictionary, where the keys are the names of an input ends and values are dictionaries.
So, mapping file is a dictionary of dictionaries (single outer dictionary, one or more inner dictionaries).
The inner dictionary has one mandatory key, namely :code:`end`, that denotes the name of the output end.
Within the inner dictionary, some metadata about particular mapping can be placed. There are two optional special keys :code:`regex` and :code:`terminal`, that do not need any value to be correctly interpreted (can be solely the key).

Tree file
=========
The tree file is used for defining the structure of the setup (how boards, connectors and cables are connected).

.. code-block:: yaml
   :caption: Example tree file.

   name: board_1
   files:
     - b_1.yaml
   nodes:
     - name: board_2_connector_1
       files:
         - b_2_c_1.yaml
     - name: board_2_connector_2
       files:
         - b_2_c_2_f_1.yaml
         - b_2_c_2_f_2.yaml

Tree file consists of nodes, each node is a dictionary.
Single node has 2 mandatory keys :code:`name`, :code:`files` and one optional key :code:`nodes`.

The :code:`name` of the node must be unique and serves as a scope for pin names within this node.
It is necessary in order to avoid pin name collisions.
Otherwise, name collisions could potentially occur in two scenarios:

#. same pin names in two different mapping files,
#. same mapping file used more than once in the tree file.

The :code:`files` is a list of mapping files that constitute a given node.
Each tree node can consist of multiple mapping files.
Thanks to this, it is possible to define mappings for different connectors located on the same board in separate files or split connector mappings into multiple files to group them by functionality.

The :code:`nodes` is a list of children nodes connected with a given node.

Assignment file
===============
The assignment file is used for defining port assignments to the terminal pins.

.. code-block:: yaml
   :caption: Example assignment file.

   _default_:
     set_property:
       IOSTANDARD: LVDS_33
       DIFF_TERM: "TRUE"
   
   board_2_connector_1:
     port[1]:
       end: end_pin_1
       set_property:
         IOSTANDARD: LVDS_25
   
   board_2_connector_2:
     port[2]:
       end: end_pin_2
       set_property:
         DIFF_TERM: "FALSE"
   
     port[3]:
       end: end_pin_3
   
     # Differential pair example
     diff_[pn]:
       node: board_2_connector_2
       end: end_diff_pin_[pn]
       regex:
   
   board_1:
     port[4]:
       end: end_pin_4
       end: s3

The assignment file can also be seen as a dictionary of dictionaries.
Within the outer dictionary, single item is a dictionary defining assignments within the particular node (except  the :code:`_default_` key, see :ref:`_default_`).
The *key* is the name of the node, and the *value* is a dictionary.

Within the inner dictionaries, single item is an assignment.
The *key* is the name of the port.
The destination pin name is placed under the :code:`end` key.
