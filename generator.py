from pathlib import Path
from openpecha.utils import load_yaml,download_pecha,_mkdir
from openpecha.core.ids import get_collection_id
import re
import logging
logging.basicConfig(level=logging.INFO,filename="changes.log",filemode="w",format="%(message)s")


class Collection:

    def __init__(self,collection_yml:Path=None):
        read_me=[]
        if collection_yml:
            self.collection = load_yaml(collection_yml)

    def log_change(self,changes):
        """
        Change format: 
        text_file,line_no,old_value,new_value
        """
        logging.INFO(changes)

    def seperate_items(self,items):
        opfs,opas = [],[]
        for item in items:
            if item.startswith("P"):
                opfs.append(item)
            elif item.startswith("A"):
                opas.append(item)        
        return opfs,opas
    
    def get_item(self,id):
        path = download_pecha(pecha_id=id)
        return path
    
    def parse_opa_meta(self,opa_file_path):
        meta = load_yaml(opa_file_path / "meta.yml")
        alignment_to_base = meta["alignment_to_base"]
        associated_pechas = meta["pechas"]
        return alignment_to_base.values()
        
    def parse_opas(self,opas):
        views = {}
        """
        views = {
            "opa_id":{
                "lang":text
            }
        }
        """
        for opa in opas:
            view = self.parse_single_opa(opa)
            views.update({opa:view})
        return views

    def parse_single_opa(self,opa):
        opa_file_path = self.get_item(opa)
        #alignment_yml = self.parse_opa_meta(opa_file_path / f"{opa_file_path.name}.opa")
        alignment_base = self.get_alignment_base(opa_file_path / f"{opa_file_path.name}.opa")
        alignment = load_yaml(alignment_base)
        view = self.create_view(alignment,opa_file_path.name)
        return view

    def get_alignment_base(self,opa_path:Path):
        for file in opa_path.iterdir():
            if file.name != "meta.yml":
                return file


    def get_layers(self,segment_sources):
        item_to_layer={}
        """"
        item_to_layer={"pecha_id":{
            "base":base_text,
            "segment_layer":segment_layer
        }}
        """
        for pecha_id in segment_sources.keys():
            base = segment_sources[pecha_id]["base"]
            pecha_path = self.get_item(pecha_id)
            base_text = Path(pecha_path / f"{pecha_id}.opf/base/{base}.txt").read_text(encoding="utf-8")
            segment_layer = load_yaml(Path(pecha_path /f"{pecha_id}.opf/layers/{base}/Segment.yml"))
            meta = load_yaml(Path(pecha_path /f"{pecha_id}.opf/meta.yml"))
            item_to_layer.update({pecha_id:{
                "base":base_text,
                "segment_layer":segment_layer
            }})
        
        return item_to_layer


    def create_view(self,alignment,alignment_id):
        view = {}
        """
        view = {
            "lang":text
        }
        """
        segment_sources = alignment["segment_sources"]
        segment_pairs = alignment["segment_pairs"]
        item_to_layer = self.get_layers(segment_sources)
        
        for ann_id in segment_pairs.keys():
            for pecha_id,seg_id in segment_pairs[ann_id].items():
                base_text = item_to_layer[pecha_id]["base"]
                segment_ann = item_to_layer[pecha_id]["segment_layer"]["annotations"]
                span = segment_ann[seg_id]["span"]
                segment_text = base_text[span["start"]:span["end"]]
                lang = segment_sources[pecha_id]["lang"]
                if lang not in view.keys():
                    view.update({lang:segment_text})
                else:
                    view.update({lang:view[lang]+"\n"+segment_text}) 
                self.update_readme(pecha_id,alignment_id,)  
        return view

    def write_views(self,views):
        collection_id = get_collection_id()
        collection_main_folder = f"{collection_id}-textpairs"
        _mkdir(Path(collection_main_folder))
        for opa_id,body in views.items():
            for lang,text in body.items():
                Path(f"{collection_main_folder}/{opa_id}-{lang}.txt").write_text(text)


    def parse_opfs(self,opfs):
        for opf in opfs:
            self.parse_single_opf(opf)

    def parse_single_opf(opf):
        pass

    def export_collection(self):
        items = self.collection["items"]
        opfs,opas = self.seperate_items(items)
        views = self.parse_opas(opas)
        self.write_views(views)

if __name__ == "__main__":
    yml_path = Path("C235865.yml")
    obj = Collection(yml_path)
    obj.export_collection()
    
    

    
