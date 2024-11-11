terraform {
  required_providers {
    aviatrix = {
      source  = "AviatrixSystems/aviatrix"
      version = "3.1.5"
    }
  }
  backend "azurerm" {
    resource_group_name  = "avx-mgmt-rg"
    storage_account_name = "labtestazuretstg"
    container_name       = "tfstate"
    key                  = "kddc.dcf.terraform.tfstate"
  }
}

provider "aviatrix" {
  controller_ip = var.controller_ip
  username      = var.username
  password      = var.password
}

# $ export AVIATRIX_USERNAME="admin"
# $ export AVIATRIX_PASSWORD="password"
