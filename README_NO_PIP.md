To run the GMD CLI app directly from git (without pip install):                                                                                                                                                       
                                                                                                                                                                                                                      
## Option 1: Using Python Module (-m)                                                                                                                                                                                 
                                                                                                                                                                                                                      
```bash                                                                                                                                                                                                               
# From the cloned repository root                                                                                                                                                                                     
cd gmd                                                                                                                                                                                                                
                                                                                                                                                                                                                      
# Run gmd-merge                                                                                                                                                                                                       
python -m gmd.cli.merge -M /path/to/master -S /path/to/slave                                                                                                                                                          
                                                                                                                                                                                                                      
# Run gmd-commit                                                                                                                                                                                                      
python -m gmd.cli.commit -M /path/to/repo -m "message"                                                                                                                                                                
                                                                                                                                                                                                                      
# Run gmd-gui                                                                                                                                                                                                         
python -m gmd.gui.main                                                                                                                                                                                                
```                                                                                                                                                                                                                   
                                                                                                                                                                                                                      
## Option 2: Using Direct Script Paths                                                                                                                                                                                
                                                                                                                                                                                                                      
```bash                                                                                                                                                                                                               
# From the cloned repository root                                                                                                                                                                                     
cd gmd                                                                                                                                                                                                                
                                                                                                                                                                                                                      
# Run merge CLI                                                                                                                                                                                                       
python gmd/cli/merge.py -M /path/to/master -S /path/to/slave                                                                                                                                                          
                                                                                                                                                                                                                      
# Run commit CLI                                                                                                                                                                                                      
python gmd/cli/commit.py -M /path/to/repo -m "message"                                                                                                                                                                
                                                                                                                                                                                                                      
# Run GUI                                                                                                                                                                                                             
python gmd/gui/main.py                                                                                                                                                                                                
```                                                                                                                                                                                                                   
 
## Option 3: Install in Editable Mode (Recommended for Development)
 
```bash
# Clone the repo
git clone https://github.com/w4d4f4k/gmd.git
cd gmd
 
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
 
# Install dependencies
pip install -r requirements.txt
 
# Install in editable/development mode
pip install -e .
 
# Now you can use the commands normally:
gmd-merge -M /path/to/master -S /path/to/slave
gmd-commit -M /path/to/repo -m "message"
gmd-gui
```
 
## Requirements Before Running
 
Make sure you have the dependencies installed:
```bash
pip install rich pydantic PyYAML click
```
 
For GUI (if needed):
```bash
# tkinter is usually included with Python, but verify:
python -c "import tkinter"
 
# Optional for enhanced icons:
pip install Pillow
```
 
## Quick Test
 
```bash
# Test if it works
python -m gmd.cli.merge --help
```
 
The `-e` (editable) install is best for development since changes to the code are immediately reflected without reinstalling!
