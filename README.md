Hello! Welcome to the STMUN Backend Code repository. The files here are designed to help us run the conference and manage our club day-to-day.
They are sorted into folders based on who uses it, which contain programs inside. The language I used was Python, and I largely tried to follow
the Object Oriented Programming paradigm (don't worry if you don't know what that is!). You will notice some infrastructure files, which
contain helper functions that directly interact with our services. They are designed to be blind to our business logic (mostly), so swapping 
services in the future should be quite easy. 

Note to club:
If you aren't good at tech or understand code, please refrain from editing the source code. If an error is thrown back, screenshot it and contact
the USG of Logistics. Don't try fixing things yourself...and above all don't vibe code without understanding the output. Also, remember that this repo is public!

Structure of files:
`````
STMUN-Backend-Code
|-- Finances Automations
   |-- CopyingInvoices.py
   |-- FinancesAutomation.py
   |-- InvoiceFinalData.py
|-- PR Automations
   |-- CopyBadges.py
   |-- CopyPlacards.py
|-- SG Automations
   |-- Assignments.py
   |-- IndividualSheets.py

`````
