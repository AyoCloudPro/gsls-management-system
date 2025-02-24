terraform {
  required_providers {
    google = {
      source = "hashicorp/google"
      version = "6.21.0"
    }
  }
}

provider "google" {
  # Configuration options
  project     = "turnkey-pottery-446722-m3"
  region      = "africa-south1"
  credentials = var.credentials
}

