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

The :code:`terminal` key functions like a type annotation.
By default end pins are not intended to be connected to the FPGA ports.
To indicate, that the end pin must be connected to the port, a special property called terminal must be added to this end pin.
What is more, nothing more can be mapped to the pin marked as terminal.
To some extent, this mechanism is similar in its nature to the mutability aspect of the Rust programming language and provides the basics for extensive mistakes detection.
Terminal pins can be defined in each node of the tree, they are *not* limited only to the leaf nodes.

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
