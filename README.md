# A simple catalog application developed in Python (Flask)

## Demo

http://34.228.221.76/

## Description

A simple web application different catalogs and the content of each. The application allows the user to register via a Google Account and can add catalogs and items. Items can only be edited or modified by the user who created them. Furthermore, APIs provide access to the catalogs and their contents.

## Installation

- Install Vagrant and VirtualBox
- Clone the fullstack-nanodegree-vm repository.
- Uncompress this project folder in the `/vagrant` folder
- Launch the Vagrant VM
- Access the folder containing the project `cd /vagrant`
- Setup the database by running `python database_setup.py`
- Populate the database `python populate_db.py`
- And finally run the application within the VM by typing `python application.py`
- Access and test your application by visiting http://localhost:5000 locally on your browser.
