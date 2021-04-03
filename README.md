# UltraHydro
UltraHydrophonics Scan Tank Development

##How to Set Up a Computer for this Application:

Requirements:
Windows 10 64 bit

Install PicoSDK 64 bit
https://www.picotech.com/downloads/_lightbox/pico-software-development-kit-64bit

Install GcLib
https://www.galil.com/sw/pub/win/gclib/galil_gclib_480.exe

Install Anaconda 3 with Python 3.8.6
________________________________________________________
Run the following commands in the anaconda prompt with a fresh environment:

>conda install -c conda-forge pyside2 \
>conda install -c conda-forge pyqt5-sip \
>conda install -c conda-forge h5py \
>conda install -c conda-forge pyyaml \
>conda install -c conda-forge pyqtgraph \
>conda install -c conda-forge pyvisa 

Set up gclib, assuming it is already installed

>cd %temp% \
>mkdir py \
>cd py \
>copy "c:\Program Files (x86)\Galil\gclib\source\wrappers\python\*" . \
>copy "c:\Program Files (x86)\Galil\gclib\examples\python\*" . \
>python setup.py install

Set up picotech library, assuming picoSDK is istalled
* First you must download the picoscope python wrappers folder from GitHub
    * https://github.com/picotech/picosdk-python-wrappers
* Then, extract the folder and navigate to it in the anaconda terminal (same environment)
* Finally, run this command.

>python install setup.py 

When you are finished, run this command to verify the anaconda environment has all of these libraries:

>conda list

the output should resemble this:

Name   |                    Version       |            Build | Channel
--------------------|---------------------|------------------|----------
ca-certificates     |      2020.12.5      |      h5b45459_0  |  conda-forge
cached-property     |      1.5.1          |            py_0  |  conda-forge
certifi             |      2020.12.5      |  py38haa244fe_1  |  conda-forge
console_shortcut    |      0.1.1          |              4    |
gclib               |      1.0            |          pypi_0  |  pypi
gettext             |      0.19.8.1         | h1a89ca6_1005   | conda-forge
glib                |      2.66.4         |      h885f38d_2   | conda-forge
glib-tools          |      2.66.4           |    h885f38d_2   | conda-forge
h5py                |      3.1.0       |    nompi_py38h022eade_100  |  conda-forge
hdf5                |      1.10.6      |    nompi_h5268f04_1114  |  conda-forge
icu                 |      68.1         |        h0e60522_0  |  conda-forge
intel-openmp        |      2020.3       |      h57928b3_311  |  conda-forge
jpeg                |      9d            |       h8ffe710_0  |  conda-forge
krb5                |      1.17.2        |       hbae68bd_0  |  conda-forge
libblas              |     3.9.0          |           7_mkl  |  conda-forge
libcblas             |     3.9.0          |           7_mkl  |  conda-forge
libclang             |     11.0.1   |       default_h5c34c98_1  |  conda-forge
libcurl              |     7.71.1       |        h4b64cdc_8  |  conda-forge
libffi               |     3.3          |        h0e60522_2  |  conda-forge
libglib              |     2.66.4       |        h48f9de8_2  |  conda-forge
libiconv             |     1.16         |        he774522_0  |  conda-forge
liblapack            |     3.9.0        |             7_mkl  |  conda-forge
libpng               |     1.6.37       |        h1d00b33_2  |  conda-forge
libssh2              |     1.9.0        |        hb06d900_5  |  conda-forge
libxml2              |     2.9.10       |        hf5bbc77_3  |  conda-forge
libxslt              |     1.1.33       |        h65864e5_2  |  conda-forge
mkl                  |     2020.4       |      hb70f87d_311  |  conda-forge
numpy                |     1.19.5       |    py38h0cc643e_1  |  conda-forge
openssl              |     1.1.1i       |        h8ffe710_0  |  conda-forge
pcre                 |     8.44         |        ha925a31_0  |  conda-forge
picosdk              |     1.0          |            pypi_0  |  pypi
pip                  |     21.0         |      pyhd8ed1ab_1  |  conda-forge
pyqt5-sip            |     4.19.18      |    py38h885f38d_7  |  conda-forge
pyqtgraph            |     0.11.1       |      pyhd3deb0d_0  |  conda-forge
pyreadline           |     2.1          |   py38haa244fe_1003|    conda-forge
pyside2              |     5.13.2       |    py38hadd4fab_4  |  conda-forge
python               |     3.8.6        |   h7840368_5_cpython |   conda-forge
python_abi           |     3.8          |            1_cp38   | conda-forge
pyvisa               |     1.11.3       |    py38haa244fe_1   | conda-forge
pyyaml               |     5.4.1        |    py38h294d835_0   | conda-forge
qt                   |     5.12.9       |        h5909a2a_3   | conda-forge
setuptools           |     49.6.0       |    py38haa244fe_3   | conda-forge
sqlite               |     3.34.0       |        h8ffe710_0   | conda-forge
tk                   |     8.6.10       |        h8ffe710_1   | conda-forge
typing_extensions    |     3.7.4.3      |              py_0   | conda-forge
vc                   |     14.2         |        hb210afc_2   | conda-forge
vs2015_runtime       |     14.28.29325  |        h5e1d092_0   | conda-forge
wheel                |     0.36.2       |      pyhd3deb0d_0   | conda-forge
wincertstore         |     0.2          |   py38haa244fe_1006 |   conda-forge
yaml                 |     0.2.5        |        he774522_0   | conda-forge
zlib                 |     1.2.11       |     h62dcd97_1010   | conda-forge

____________________________________________________________________________

# Github Workflow

## Getting Setup in Pycharm

1. Close the previous project (scan_tank) with File > Close Project
2. On the welcome screen, click "Get from VCS"
3. Log into Github, and download git if you see the prompt
4. Click on your github account, choose this repository and click clone
5. The project has been cloned onto your machine! Finally, configure your interpreter so that Pycharm uses our anaconda environments.

## Feature Development

1. When you are ready to develop a feature, open the repository on Github.com
2. Find the branch drop down menu
3. Type the name of your branch and click create branch, it should say that you are branching from the master branch
4. The branch has been created in the origin, the team can see your branch but in order to begin development you must check out the branch locally
5. In Pycharm, update the project with the blue arrow
6. In the bottom right, click on the branch menu, you should see your new branch as "origin/yourbranchname" under remote branches
7. Click on your remote branch and then click checkout

## Pull Requests

Your new feature is tested and stable, now it's time to merge your branch with the master branch!

1. On Github.com click on Pull Requests
2. There are two dropdown menus, one called "base" and one called "compare"
3. Select the master branch in the base menu and your branch in the compare menu, click "Create Pull Request", regardless of whether there are merge conflicts
4. Write a good title, and a short summary of what you will be adding/changing
5. When you are done, click create pull request again and notify the team

### Code Reviews

Part of this workflow includes code reviews. You must obtain one approving code review from one of your teammates before your code can be merged into the master branch. **Github will not let you merge without one.** This allows us to double check our code, and ensures that at least two people know what is happening with each change.

You can request a code review by clicking on the gear next to reviewers, this will let you type in your desired teammates username to request a review from them.

### Writing a Review

1. Open your teammates pull request, you can start a review by adding a comment to a specific line or by clicking on Start Review.
2. Look over what your teammate is changing. Add comments and constructive feedback where it is needed.
3. If everything looks good and github is able to merge the branches automatically, click on the review changes button, write a short summary and tick one of the three options below
    * Comment - Submits general feedback without explicit approval
    * Approve - Submits feedback with the approval to merge changes
    * Request - Submits feedback that must be addressed before merging
    
### Testing Code

We are able to test changes and resolve conflicts locally before merging our changes on the website.

A PR is a request for the branch to be merged, you can still work on your branch and push changes to the origin, those changes will show up in your pull request!

This allows you to
   * Make requested changes
   * Merge your local feature branch with your local master branch and test your code without worry

#### Merging Locally

1. Checkout your feature branch in Pycharm and make sure that your local master branch is up to date
2. Click on Git > Merge..., select master. This merges the local master branch into your local feature branch. This may sound backwards, but keep in mind the PR exists on your feature branch, not the master. The master branch cannot be pushed to directly, so if you merge your local feature branch into your local master branch you will be stuck
3. When the conflicts window opens, click on Merge
4. Examine and resolve each conflict. Sometimes you may want your changes, their changes, or both.
5. When the conflicts are resolved, you can test our your merged code and see how it runs
6. If something is wrong, you can always start over by deleting both local branches and checking them out again. This will bring you back to step 1
7. When you are satisfied with your merged code, push your changes to your feature branch in the origin! They will be reflected in the PR, and the reviewer will be able to see your merged code
