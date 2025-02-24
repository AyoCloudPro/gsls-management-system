# Create a vpc
# =========================
resource "google_compute_network" "main" {
  name                                      = "gsls-vpc"
  routing_mode                              = "REGIONAL"
  auto_create_subnetworks                   = false
  mtu                                       = 1460
  delete_default_routes_on_create           = false
}


# Create a subnet
# =======================
resource "google_compute_subnetwork" "gsls-subnetwork" {
  name          = "gsls-subnetwork"
  ip_cidr_range = "10.2.0.0/16"
  region        = "africa-south1"
  network       = google_compute_network.main.id
  secondary_ip_range {
    range_name    = "tf-test-secondary-range-update1"
    ip_cidr_range = "192.168.10.0/24"
  }
}


# Create a vm
# =============================================================
resource "google_compute_instance" "gsls-vm" {
  name         = "gsls-vm"
  machine_type = "e2-medium"
  zone         = "africa-south1-a"

  network_interface {
    network    = google_compute_network.main.id
    subnetwork = google_compute_subnetwork.gsls-subnetwork.id
    access_config {
      // External IP (can be set to 'null' if you don't need one)
    #   nat_ip = google_compute_address.gcp_static_ip.address
      
    }
  }

  boot_disk {
    initialize_params {
      image = "debian-cloud/debian-11"
      labels = {
        my_label = "value"
      }
    }
  }
      // Optional config to make the instance ephemeral
  scheduling {
    preemptible       = true
    automatic_restart = false
  }

  service_account {
    # Google recommends custom service accounts that have cloud-platform scope and permissions granted via IAM Roles.
    email  = "terraform-auto@turnkey-pottery-446722-m3.iam.gserviceaccount.com"
    scopes = ["https://www.googleapis.com/auth/cloud-platform"]
  }

  shielded_instance_config {
    enable_secure_boot          = true
    enable_vtpm               = true  # Recommended: Enable vTPM as well
    enable_integrity_monitoring = true # Recommended: Enable integrity monitoring
  }
}
