from pathlib import Path
from openpecha.utils import load_yaml,download_pecha,_mkdir
from openpecha.core.ids import get_collection_id
from openpecha.core.layer import Layer, LayerEnum
import re
import logging
import csv
from openpecha import config
from openpecha.core.pecha import OpenPechaFS
from openpecha.core.metadata import CollectionMetadata

logging.basicConfig(level=logging.INFO,filename="catalog.log",filemode="w",format="%(message)s")



class Collection:
    def __init__(self,collection_yml:Path=None):
        self.type_of_layers = set()
        self.no_of_text = 0
        self.no_of_aligned_seg = 0
        self.read_me=[]
        self.lang_seg_count = {}
        if collection_yml:
            collection = load_yaml(collection_yml)
            self.collection = CollectionMetadata(**collection)


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
    
    def get_item(self,id,output=None):
        
        if re.match(r'^A',id):
            path = Path(f"/Users/jungtop/Dev/lotsawa_house_parser/zot_dir_v1/opas/{id}")
        else:
            path = Path(f"/Users/jungtop/Dev/lotsawa_house_parser/zot_dir_v1/opfs/{id}")
        #path = download_pecha(pecha_id=id,out_path=output)
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
                "lang":text
        }
        """
        for opa in opas:
            view,alignment_meta = self.parse_single_opa(opa)
            yield {"view":view,"opa_id":opa,"meta":alignment_meta}

    def parse_single_opa(self,opa):
        print(opa)
        opa_file_path = self.get_item(opa)
        #alignment_yml = self.parse_opa_meta(opa_file_path / f"{opa_file_path.name}.opa")
        alignment_base = self.get_alignment_base(opa_file_path / f"{opa_file_path.name}.opa")
        alignment = load_yaml(alignment_base)
        alignment_meta = load_yaml(opa_file_path / f"{opa_file_path.name}.opa/meta.yml")
        view = self.create_view(alignment,opa_file_path.name)
        return view,alignment_meta

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
                "segment_layer":segment_layer,
                "meta":meta
            }})
        
        return item_to_layer


    def create_view(self,alignment,alignment_id):
        view = {}
        """
        view = {
            "lang":text
        }
        """
        view_meta = {}
        segment_sources = alignment["segment_sources"]
        segment_pairs = alignment["segment_pairs"]
        item_to_layer = self.get_layers(segment_sources)
        self.no_of_text+=len(segment_sources.keys())
        
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
                #self.update_readme(pecha_id,alignment_id,item_to_layer,lang)  
                self.update_lang_seg_count(lang)
            self.no_of_aligned_seg+=1
        return view

    def update_lang_seg_count(self,lang):
        if lang not in self.lang_seg_count.keys():
            self.lang_seg_count[lang] = 1
        else:
            self.lang_seg_count[lang]+=1 


    def update_readme(self,pecha_id,alignment_id,item_to_layer,lang):
        meta = item_to_layer[pecha_id]["meta"]
        title = meta["source_metadata"]["title"]
        source = meta["source_metadata"]["creationtool"]
        bdrc_id = ""
        last_revision=""
        reviser = ""
        self.read_me.append([f"{alignment_id}-{lang}.txt",title,pecha_id,bdrc_id,source,last_revision,reviser])
        

    def write_view(self,view,collection_id):
        collection_main_folder = f"{collection_id}/views"
        _mkdir(Path(collection_main_folder))
        view_text = view["view"]
        view_title = view["meta"]["title"]
        opa_id = view["opa_id"]
        for lang,text in view_text.items():
            view_file_path = f"{collection_main_folder}/{opa_id}-{lang}.txt"
            Path(view_file_path).write_text(text)
            logging.info(f"{opa_id}-{lang}.txt,{view_title},{lang},'https://read.84000.co/")
        

    def create_readme(self):
        thead = ""
        tbody = ""
        no_of_text = f"|No of text | {self.no_of_text} |"
        Table = "| --- | --- |"
        Title = f"|Title |  |"
        no_of_seg = f"|No of aligned segment | {self.no_of_aligned_seg} |"
        featutres = f"|Features | {self.type_of_layers} |"
        for lang in self.lang_seg_count.keys():
            thead += f"<th>{lang}</th>"
            tbody += f"<td>{self.lang_seg_count[lang]}</td>"
            

        thead = f"<thead><tr>{thead}</tr></thead>"
        tbody = f"<tbody><tr>{tbody}</tr></tbody>"
        lang_seg_count_table = f"<table>{thead}{tbody}</table>"
        seg_count = f"|Segment Count |{lang_seg_count_table} |"

        readme = f"{Title}\n{Table}\n{no_of_text}\n{no_of_seg}\n{featutres}\n{seg_count}"
        return readme


    def parse_opfs(self,opfs):
        for opf in opfs:
            self.parse_single_opf(opf)

    def parse_single_opf(opf):
        pass

    def export_collection(self):
        collection_id = get_collection_id()
        items = self.collection.items
        opfs,opas = self.seperate_items(items)
        views = self.parse_opas(opas)
        for view in views:
            self.write_view(view,collection_id)
        readme = self.create_readme()
        Path(f"{collection_id}/readme.md").write_text(readme)

if __name__ == "__main__":
    yml_path = Path("C9228DDB8.yml")
    obj = Collection(yml_path)
    obj.export_collection()
    
    

    
