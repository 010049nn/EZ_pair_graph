# EZ_pair_graph
Copyright (c) 2025. RIKEN All rights reserved.  
This repository is for academic and non-commercial research use only.  
The underlying technology is currently under patent application.   
Commercial use is prohibited without a separate license agreement.  
E-mail: akihiro.ezoe at riken.jp

For testing plots
Make the script executable with:
```chmod +x pipeline_for_EZ_plot.sh```

Then run it with:
```./pipeline_for_EZ_plot.sh input_file```  

The intermediate file clustered_data.txt contains the input data with an additional cluster number column.
By setting this cluster number, it becomes possible to combine with any clustering method.
Once saved as clustered_data.txt and the shell file procedures from step 2 onwards are executed, processing will be performed based on the arbitrary cluster numbers.

Output format is an editable PDF, enabling seamless incorporation into figures. The following images have been modified.


![Image](https://github.com/user-attachments/assets/f91cde18-4acd-4082-bd2e-3735907b1e3b)
