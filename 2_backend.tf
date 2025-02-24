terraform { 
  cloud { 
    
    organization = "GSLS" 

    workspaces { 
      name = "management-system" 
    } 
  } 
}