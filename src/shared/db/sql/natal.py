class Natal:
    natal_location_cnt = "select count(*) from working.w_location"
    natal_admin1_cnt = "select count(*) from raw.admin1"
    natal_admin2_cnt = "select count(*) from raw.admin2"
    natal_cities_cnt = "select count(*) from raw.cities"
    natal_iso_country_cnt = "select count(*) from raw.iso_country"
    natal_iso_subdivision_cnt = "select count(*) from raw.iso_subdivision"

    def get(self, p_name: str) -> str:
        return getattr(self, p_name)
