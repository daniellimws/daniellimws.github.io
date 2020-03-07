---
layout: post
title: Using Vivado on Mac and VS Code
---

This semester, I am learning to program a FPGA using **Verilog** in my **Digital Fundamentals** class. We are using the **Vivado IDE** to program a bitstream for the **Digilent Basys3 Development Board**.

![basys3][basys3]

But one big problem. There is no MacOS version of Vivado. This means I need to choose either dual booting Windows/Linux or run a virtual machine. I definitely do not want to dual boot just for an IDE, so I chose to set up a Lubuntu virtual machine on VirtualBox.
Another problem is the IDE is more than 20GBs in size, and runs on Swing, so the memory usage is really high as well.

At first, I think it should be fine, as I allocated 4 CPUs and 4GBs RAM for the virtual machine. But even so, there are occasions when the interface becomes very laggy and it feels so hard to do actual work on it. There must be a better way... (and it's still not dual booting).

And I realized, that the Vivado IDE runs some commands in the Tcl (Tool command language) console whenever I perform an action (e.g. add a design source, run simulation). I wondered if I can run these commands in the command line, and if so I would not need to use the GUI anymore.

![vivado-tcl][vivado-tcl]

*<center>Vivado Tcl Console</center>*
<br/>

What I did next was to perform all the actions I would normally do, starting from creating a project, adding design sources, up to running simulations and generating a bitstream. I recorded the commands called by the IDE for each of these actions.

Later, I found out that one can indeed run Tcl commands through the Vivado command line tool. In addition, it is also possible to save the commands in a .tcl file and run all the commands at once.

![tcl-cli][tcl-cli]

At this point, I decided to try out all the commands recorded earlier and see if I could replicate the actions performed in the IDE. With the help of the [Vivado Tcl Command Reference Guide](https://www.xilinx.com/support/documentation/sw_manuals/xilinx2018_2/ug835-vivado-tcl-commands.pdf), I was able to find all the commands I needed for my typical workflow and put them in a series of scripts [here](https://github.com/daniellimws/vivado-mac/tree/master/shared/viv/scripts).

Now that I figured it is possible to use Vivado entirely from the command line, and at the same time found this [Docker configuration](https://github.com/BBN-Q/vivado-docker) for Vivado, I deleted my Lubuntu virtual machine, and set up a Vagrant box instead. I installed Vivado on it based on the commands used for the Docker setup, and have documented the steps and config files needed [here](https://github.com/daniellimws/vivado-mac).

But I am still not satisfied. Currently my Tcl scripts are just templates, and I would need to replace the project name and file names in the scripts for them to actually work. Ain't nobody got time for that. So, I developed a [VS Code extension](https://github.com/daniellimws/viv/) that automates these processes for me, and allows me to call these commands straight from inside VS Code as I write my code.

![vscode][vscode]

With all these in place, this is how a typical workflow looks like. By the way, although Vagrant machines only have the CLI, it is possible to still access the GUI with the help of XQuartz.

<iframe width="560" height="315" src="https://www.youtube.com/embed/rCPUdh8m8rM" frameborder="0" allow="accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>

Currently, my Tcl scripts are customized for my own setup, but if you are interested in using them and want to modify them, feel free to ask me for more information.


[basys3]:{{site.baseurl}}/images/vivado-on-mac/basys3.jpg
[vivado-tcl]:{{site.baseurl}}/images/vivado-on-mac/vivado-tcl.png
[tcl-cli]:{{site.baseurl}}/images/vivado-on-mac/tcl-cli.png
[vscode]:{{site.baseurl}}/images/vivado-on-mac/vscode.png