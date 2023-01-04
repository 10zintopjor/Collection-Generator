from pathlib import Path
from uuid import uuid4
from copy import deepcopy
from datetime import date, datetime
import yaml
import random
import logging
from openpecha.utils import download_pecha
from openpecha.utils import load_yaml
from openpecha.core.layer import LayerEnum
from openpecha.core.pecha import OpenPechaFS


logging.basicConfig(level=logging.INFO,filename="changes.log",filemode="w",format="%(message)s")


class  Collection:
    @staticmethod
    def get_collection_id():
        return "C"+"".join(random.choices(uuid4().hex, k=8)).upper()
    
    @staticmethod
    def get_op_work_id():
        return "W"+"".join(random.choices(uuid4().hex, k=6)).upper()

    def create_collection(self,collectionYml:Path):
        collection_id = self.get_collection_id()
        collection = load_yaml(collectionYml)
        pecha_paths = self.download_files(collection["items"])
        self.create_bases(pecha_paths)
        """ opa_id = opa_path.stem
        bases = Path(opa_path/f"{opa_id}.opa").iterdir()
        for base in bases:
            alignment = self.from_yml(Path(base/"Alignment.yml"))
            view = self.get_views(alignment,base.stem)
            self.write_view(view,collection_id) """
        return pecha_paths


    def create_bases(self,opa):
        pass


    def download_files(self,items):
        pecha_paths = []
        for item in items:
            pecha_path = self.download_file(item)
            pecha_paths.append(pecha_path)
        return pecha_paths
    
    def download_file(self,item):
        pecha_path = download_pecha(item,out_path="./pechas")
        return pecha_path
        
    def write_view(self,view,collection_id):
        work_id = self.get_op_work_id()
        for lang in view.keys():
            work_dir = Path(f"{collection_id}/{work_id} ")
            if not work_dir.is_dir():
                work_dir.mkdir(exist_ok=True, parents=True)
            Path(f"{collection_id}/{work_id}/{work_id}-{lang}.txt").write_text(view[lang])

    def get_views(self,alignment,base):
        view = {}
        source_opfs = alignment["segment_sources"].keys()
        seg_pairs = alignment["segment_pairs"]
        for seg_pair_id in seg_pairs.keys():
            for source_opf in source_opfs:
                lang = alignment["segment_sources"][source_opf]["language"]
                seg_id = seg_pairs[seg_pair_id][source_opf]
                seg_text = self.get_seg_text(source_opf,base,seg_id)
                view[lang] = (view[lang]+"\n" if lang in view.keys() else "")+seg_text
        return view 

    def get_seg_text(self,source_opf,base,seg_id):
        seg_layer_path = f"{source_opf}/{source_opf}.opf/layers/{base}/Segment.yml"
        seg_layer = self.from_yml(Path(seg_layer_path))
        annotations = seg_layer["annotations"]
        span = annotations[seg_id]["span"]
        base_text = Path(f"{source_opf}/{source_opf}.opf/base/{base}.txt").read_text(encoding="utf-8")
        seg_text = base_text[span["start"]:span["end"]].replace("\n"," ")
        return seg_text

    def from_yml(self,yml_path:Path):
        dic = yaml.safe_load(yml_path.read_text())
        return dic

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
    

    def log_change(self,changes):
        """Chnages format 
        source_realtive_path,line_no,old_value,new_value
        """
        logging.INFO(changes)
    
    def is_work_id_avaiabale(self,work_id):
        pass


pecha = OpenPechaFS()
segment_layer = pecha.get_layer("1234",LayerEnum.segment)
segment_layer.get_annotations
collection_path = Path("C235865.yml")
obj =Collection()
obj.create_collection(collection_path)
#opa_path = Path("AEC38C4A4")
#obj.create_collection(opa_path)