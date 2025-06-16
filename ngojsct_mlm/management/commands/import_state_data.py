from django.core.management.base import BaseCommand
import pandas as pd
from ngojsct_mlm.models import StateModel, CityModel  # Import your models
import os
import logging
from django.conf import settings
from django.utils import timezone
import datetime

class Command(BaseCommand):
    help = 'Generate fake data for all models'

    def handle(self, *args, **kwargs):
        import_data_csv()

def import_data_csv():
    # from models import DistrictMasterModel, BlockMasterModel, GramPanchayatMasterModel, VillageMasterModel  # Import your models

    # Configure logging to write to a file
    log_file_path =os.path.join(settings.BASE_DIR, "protected_data", 'logfile1.log')  # Specify the path where you want the log file to be saved
    logging.basicConfig(
        filename=log_file_path, 
        level=logging.INFO, 
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    # Read CSV
    csv_file_path = os.path.join(settings.BASE_DIR, "protected_data", "list_of_cities_and_towns_in_india-834j.csv")
    df=pd.read_csv(csv_file_path)
    print("IMPORT START")
    # Loop through each row in the DataFrame
    for index, row in df.iterrows():
        sno= row['S.No']
        state_name = row['State']
        name_of_city = row['Name of City']

        row_data = f"state Name: {state_name},city Name: {name_of_city}, "
        #logging.info(row_data)  # Log row data instead of print

        try:
            # Check if district exists
            state_exist = StateModel.objects.filter(name=state_name).first()
            if not state_exist:
                state_exist = StateModel.objects.create(
                    name=state_name,
                    created_at=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    updated_at=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    status=1
                )
                #logging.info(f"Created new district: {district_name}")

            # Check if block exists
            city_exist = CityModel.objects.filter(name=name_of_city,state_id=state_exist.id).first()
            if not city_exist:
                city_exist = CityModel.objects.create(
                    name=name_of_city,
                    state_id=state_exist.id,  # Use the district's ID
                    created_at=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    updated_at=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    status =1,
                )
                #logging.info(f"Created new block: {block_name}")

                logging.info(f"Created record :,{sno}")
                print(f"Created record :,{sno}")
            else:
                logging.info(f"already exist  :,{sno}")
        except Exception as e:
            logging.error(f"Failed to insert data for SN: {sno} - Error: {str(e)}")
    print("IMPORT END")