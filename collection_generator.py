from pathlib import Path
from uuid import uuid4
from copy import deepcopy
from datetime import date, datetime


class  Collection:
    def get_opa(self,opa_path):
        pass

    def get_segment_pairs(self,pecha_ids,volume,lang_with_algnmt):
        segments_ids = {}
        cur_pair = {}
        pair= {}
        seg_pairs = {}
        segment_length = ""
        last_seg_len = ""
        for pecha_id in pecha_ids:
            lang,pechaid = pecha_id
            if lang in lang_with_algnmt:
                segment_layer_path = f"{self.root_opf_path}/{pechaid}/{pechaid}.opf/layers/{volume}/Segment.yml"
                pecha_yaml = load_yaml(Path(segment_layer_path))
                ids = self.get_ids(pecha_yaml["annotations"])
                if lang == "bo":
                    segment_length = len(ids)
                segments_ids[pechaid]= ids
                last_seg_len = len(ids)
 
        if segment_length == "":
            segment_length = last_seg_len
        
        for num in range(1,segment_length+1):
            for pecha_id in pecha_ids:
                lang,pechaid = pecha_id
                if lang in lang_with_algnmt: 
                    cur_pair[pechaid]=segments_ids[pechaid][num] if num in segments_ids[pechaid] else 'None'
            pair[uuid4().hex] = deepcopy(cur_pair)
            seg_pairs.update(pair)

        return seg_pairs

    
    def create_meta(self,work_id,langs):
        
        metadata = {
            "id": work_id,
            "type": "translation",
            "source_metadata":{
                "languages":langs,
                "datatype":"PlainText",
                "created_at":datetime.now(),
                "last_modified_at":datetime.now()
                },
        }
        return metadata
