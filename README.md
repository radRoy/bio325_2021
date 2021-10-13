# bio325_2021
IT introduction for BIO325 (fall 2021)

## Installation of Git for Windows

<ol>
<li> Open a web browser and visit https://git-scm.com/download/win. </li>
<li> Download the correct software version for your operating system.</li>
<li> Start the installation and follow the instructions</li>
</ol>

## Installation of Miniconda

<ol>
<li> Open a web browser and visit https://docs.conda.io/en/latest/miniconda.html.</li>
<li> Download the correct software version for your operating system.</li>
<li> Start the installation and follow the instructions</li>
</ol>

## Create a virtual environment for Python

Windows user should execute conda commands from the anaconda prompt (has been installed together with miniconda). 
Linux and macOS users may use their default terminals

<ul>
<li> Windows: From the start menu, search for "Anaconda Prompt" and open it.</li>
<li> macOS and Linux: Open a terminal</li>
</ul>

Execute the following command in your command prompt:

    conda create -n bio325_2021 python=3.9

Once the virtual environment has been generated, activate it with this command:

    conda activate bio325_2021


## Clone the bio325_2021 github repository and install the requirements

Make sure that your virtual environment is activated. 
Execute the following commands in your command prompt:


    git clone https://github.com/jluethi/bio325_2021
    cd bio325_2021 
    pip install -r requirements.txt 


all the required python packages listed in the file "requirements.txt" will be installed.

## Download the data for the tutorial

<ol>
<li> Open a web browser and visit https://link/to/data. </li>
<li> Download the whole folder containing the data to your local machine.</li>
</ol>
