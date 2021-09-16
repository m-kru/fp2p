# fp2p - FPGA Port To Pin

fp2p is a tool for robust port to pin assignment in multi-board FPGA designs.
The implementation has two main goals, safety (check as many potential human mistakes as possible) and reusability (reuse connections mappings, defined in files, in multiple designs).
It is fully declarative and programming language-agnostic from the users perspective.

## Documentation

[Read the Docs](https://fp2p.readthedocs.io/en/latest/)

## Citation

If you find fp2p useful, and write any academic publication on a project utilizing fp2p please consider citing.

```
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
```
