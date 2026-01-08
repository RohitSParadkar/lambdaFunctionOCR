import requests
from typing import Optional, Dict
import os
from pathlib import Path
import urllib3
from dotenv import load_dotenv


# =========================
# LOAD ENV (Lambda-safe)
# =========================
load_dotenv()

# Disable SSL warnings for self-signed certificates (if needed)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class DolphinDMSClient:
    """Secure client for Dolphin DMS API operations"""
    
    def __init__(self, host_url: str, company_id: str, username: str, password: str, verify_ssl: bool = False):
        """
        Initialize the Dolphin DMS client
        
        Args:
            host_url: The host URL 
            company_id: Your company/repository ID
            username: API username
            password: API password
            verify_ssl: Whether to verify SSL certificates (default: False for self-signed certs)
        """
        self.host_url = host_url.rstrip('/')
        self.company_id = company_id
        self.username = username
        self.password = password
        self.auth = (username, password)
        self.verify_ssl = verify_ssl
        self.session = requests.Session()
        self.session.auth = self.auth
        self.session.verify = verify_ssl
        
        # Debug info (masked password)
        print(f"Client initialized:")
        print(f"  Host: {self.host_url}")
        print(f"  Company ID: {self.company_id}")
        print(f"  Username: {self.username}")
        print(f"  Password: {'*' * len(self.password) if self.password else 'NOT SET'}")
        print()
        
    def upload_document(
        self,
        file_path: str,
        channel: str = "Worksite",
        policy_number: Optional[str] = None,
        insured_name: Optional[str] = None,
        insured_contact_no: Optional[str] = None,
        insurance_company_name: Optional[str] = None,
        products: Optional[str] = None,
        policy_start_date: Optional[str] = None,
        policy_expiry_date: Optional[str] = None,
        sum_assured_or_idv: Optional[str] = None,
        net_premium: Optional[str] = None,
        vehicle_registration_no: Optional[str] = None,
        business_or_retention_type: Optional[str] = None,
        total_premium: Optional[str] = None,
        file_param_name: str = "file",  # Changed to lowercase 'file'
        **kwargs
    ) -> Optional[Dict]:
        """
        Upload a document to Dolphin DMS with policy details
        
        Args:
            file_path: Path to the file to upload
            channel: Channel name (default: "Worksite")
            policy_number: Policy number
            insured_name: Name of insured person
            insured_contact_no: Contact number of insured
            insurance_company_name: Insurance company name
            products: Product type
            policy_start_date: Policy start date (format: DD/MM/YYYY)
            policy_expiry_date: Policy expiry date (format: DD/MM/YYYY)
            sum_assured_or_idv: Sum assured or IDV value
            net_premium: Net premium amount
            vehicle_registration_no: Vehicle registration number
            business_or_retention_type: Business type (e.g., "Renewal")
            total_premium: Total premium amount
            file_param_name: Name of the file parameter (default: "file")
            **kwargs: Any additional parameters
            
        Returns:
            Dict containing the response with 'Mongo ID' if successful, None otherwise
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        url = f"{self.host_url}/api/docprocessing/document/"
        
        # Build query parameters
        params = {
            'companyId': self.company_id,
            'channel': channel
        }
        
        # Add optional parameters if provided
        optional_params = {
            'Policy_Number': policy_number,
            'Insured_Name': insured_name,
            'Insured_Contact_No': insured_contact_no,
            'Insurance_Company_Name': insurance_company_name,
            'Products': products,
            'Policy_Start_Date': policy_start_date,
            'Policy_Expiry_Date': policy_expiry_date,
            'Sum_Assured_OR_IDV': sum_assured_or_idv,
            'Net_Premium': net_premium,
            'Vehicle_Registration_No': vehicle_registration_no,
            'Business_Or_Retention_Type': business_or_retention_type,
            'Total_Premium': total_premium
        }
        
        # Add non-None parameters
        for key, value in optional_params.items():
            if value is not None:
                params[key] = value
        
        # Add any additional kwargs
        params.update(kwargs)
        
        try:
            file_name = Path(file_path).name
            
            with open(file_path, 'rb') as file:
                files = {file_param_name: (file_name, file)}
                
                # Some APIs require fileName as a separate parameter
                # Add it to params if not already present
                if 'fileName' not in params:
                    params['fileName'] = file_name
                
                # Prepare the full URL for debugging
                from urllib.parse import urlencode
                query_string = urlencode(params, safe='/')
                full_url = f"{url}?{query_string}"
                
                print(f"Uploading to: {url}")
                print(f"Full URL: {full_url}")
                print(f"File parameter name: '{file_param_name}'")
                print(f"File name: {file_name}")
                print(f"Parameters: {params}")
                
                response = self.session.post(
                    url,
                    params=params,
                    files=files,
                    timeout=60
                )
                
                response.raise_for_status()
                
                result = response.json()
                
                if 'Mongo ID' in result:
                    print(f"✓ Upload successful! Mongo ID: {result['Mongo ID']}")
                else:
                    print(f"✓ Upload successful! Response: {result}")
                
                return result
                
        except requests.exceptions.RequestException as e:
            print(f"✗ Upload failed: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"  Response status: {e.response.status_code}")
                if e.response.status_code == 401:
                    print(f"\n  ⚠ AUTHENTICATION ERROR:")
                    print(f"  - The username or password is incorrect")
                    print(f"  - Username used: {self.username}")
                    print(f"  - Please verify your credentials in Postman")
                    print(f"  - Make sure environment variables are set correctly")
                print(f"  Response body: {e.response.text}")
            raise
        except Exception as e:
            print(f"✗ Unexpected error: {str(e)}")
            raise
    
    def download_document(self, mongo_id: str, save_path: str) -> bool:
        """
        Download a document from Dolphin DMS
        
        Args:
            mongo_id: The Mongo ID of the document to download
            save_path: Path where the downloaded file should be saved
            
        Returns:
            True if download successful, False otherwise
        """
        url = f"{self.host_url}/download.do/{mongo_id}/{self.company_id}"
        
        try:
            print(f"Downloading from: {url}")
            
            response = self.session.get(url, timeout=60, stream=True)
            response.raise_for_status()
            
            # Create directory if it doesn't exist
            save_dir = os.path.dirname(save_path)
            if save_dir:
                os.makedirs(save_dir, exist_ok=True)
            
            # Write file in chunks to handle large files
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            file_size = os.path.getsize(save_path)
            print(f"✓ Download successful! File saved to: {save_path}")
            print(f"  File size: {file_size:,} bytes")
            
            return True
            
        except requests.exceptions.RequestException as e:
            print(f"✗ Download failed: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"  Response status: {e.response.status_code}")
                print(f"  Response body: {e.response.text[:500]}")
            raise
        except Exception as e:
            print(f"✗ Unexpected error: {str(e)}")
            raise
    
    def close(self):
        """Close the session"""
        self.session.close()


# Example usage
if __name__ == "__main__":
    # Configuration - Load from environment variables
    HOST_URL = os.getenv("HOST_URL")
    COMPANY_ID = os.getenv("COMPANY_ID")
    DMS_USERNAME = os.getenv("DMS_USERNAME")
    DMS_PASSWORD = os.getenv("DMS_PASSWORD")
    print("your credential",COMPANY_ID,DMS_USERNAME,DMS_PASSWORD)
    # Validate environment variables
    if not all([COMPANY_ID, DMS_USERNAME, DMS_PASSWORD]):
        raise ValueError("Please set COMPANY_ID, USERNAME, and PASSWORD environment variables")
    
    # Initialize client
    client = DolphinDMSClient(
        host_url=HOST_URL,
        company_id=COMPANY_ID,
        username=DMS_USERNAME,
        password=DMS_PASSWORD,
        verify_ssl=False  # Set to True if you have valid SSL certificates
    )
    
    try:
        # Upload a document with all policy details
        print("=" * 70)
        print("UPLOADING DOCUMENT")
        print("=" * 70)
        
        upload_response = client.upload_document(
            file_path="./data/test_data/data/NivaBupa/35091132202500.pdf",
            channel="Worksite",
            policy_number="35091132202500",
            insured_name="Rohit",
            insured_contact_no="33",
            insurance_company_name="Niva Bupa",
            products="4w",
            policy_start_date="02/02/2026",
            policy_expiry_date="02/02/2027",
            sum_assured_or_idv="44",
            net_premium="55",
            vehicle_registration_no="66",
            business_or_retention_type="Renewal"
        )
        
        mongo_id = upload_response.get('Mongo ID')
        
        # Download the document
        if mongo_id:
            print("\n" + "=" * 70)
            print("DOWNLOADING DOCUMENT")
            print("=" * 70)
            
            client.download_document(
                mongo_id=mongo_id,
                save_path="downloads/downloaded_file.pdf"
            )
    
    except Exception as e:
        print(f"\nError: {e}")
    
    finally:
        client.close()
        print("\n✓ Session closed")