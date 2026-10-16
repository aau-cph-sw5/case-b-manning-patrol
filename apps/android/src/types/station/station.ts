/* 
Initial Station and StationArea type
Might need to be changed since readme and actual schema are conflicting 
*/
type UUID = string ;
type Area = "platform" | "concourse";

type StationArea = {
    beacon_id: UUID 
    slug: string
    last_manned_at: Date 
    current_steward_id: UUID[]
    area_type: Area  
};

export type Station = {
    station_id: UUID
    slug: string 
    areas: StationArea[]
    station_name: string 
};