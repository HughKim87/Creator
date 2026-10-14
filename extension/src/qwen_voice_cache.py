"""Local reusable voice prompts; numerical arrays only, never pickle."""
import hashlib
import json
import os
import tempfile
from collections import OrderedDict
from pathlib import Path

import numpy as np
import torch
from qwen_tts.inference.qwen3_tts_model import VoiceClonePromptItem


class VoicePromptCache:
    def __init__(self, directory, namespace):
        self.directory = Path(directory)
        self.namespace = namespace
        self.memory = OrderedDict()
        self.file_hashes = {}

    def _key(self, reference, transcript):
        path = Path(reference).resolve()
        stat = path.stat()
        identity = (str(path), stat.st_size, stat.st_mtime_ns)
        digest = self.file_hashes.get(identity)
        if digest is None:
            h = hashlib.sha256()
            with path.open("rb") as stream:
                for block in iter(lambda: stream.read(1024 * 1024), b""):
                    h.update(block)
            digest = h.hexdigest()
            self.file_hashes[identity] = digest
        return hashlib.sha256((self.namespace + "\0" + digest + "\0" + transcript).encode()).hexdigest()

    def active_key(self):
        try:
            active = json.loads((self.directory / "active.json").read_text(encoding="utf-8"))
        except FileNotFoundError:
            return None
        key = active.get("key", "")
        if active.get("namespace") != self.namespace:
            return None
        if len(key) != 64 or any(c not in "0123456789abcdef" for c in key):
            raise ValueError("저장된 목소리 정보를 확인할 수 없습니다. 녹음을 다시 등록하세요.")
        return key

    def _activate(self, key):
        self.directory.mkdir(parents=True, exist_ok=True)
        target = self.directory / "active.json"
        temporary = target.with_suffix(".new")
        temporary.write_text(json.dumps({"key": key, "namespace": self.namespace}), encoding="utf-8")
        os.replace(temporary, target)

    def _remember(self, key, value):
        self.memory[key] = value
        self.memory.move_to_end(key)
        while len(self.memory) > 4:
            self.memory.popitem(last=False)

    def acquire(self, reference, transcript, build):
        if reference:
            if not transcript:
                raise ValueError("새 녹음에는 해당 발화문 또는 SRT도 입력하세요.")
            key = self._key(reference, transcript)
        else:
            key = self.active_key()
            if not key:
                raise ValueError("먼저 목소리를 등록하세요. 등록 후에는 대본만 입력하면 됩니다.")
        if key in self.memory:
            prompts, notice = self.memory[key]
            self.memory.move_to_end(key)
            self._activate(key)
            return prompts, notice, "memory"
        location = self.directory / (key + ".npz")
        if location.is_file():
            if location.stat().st_size > 10 * 1024 * 1024:
                raise ValueError("저장된 목소리 파일이 올바르지 않습니다. 다시 등록하세요.")
            with np.load(location, allow_pickle=False) as data:
                metadata = json.loads(str(data["metadata"].item()))
                if metadata["namespace"] != self.namespace:
                    raise ValueError("모델이 바뀌었습니다. 목소리를 다시 등록하세요.")
                code = torch.from_numpy(data["ref_code"].copy())
                embedding = torch.from_numpy(data["embedding"].copy()).to(getattr(torch, metadata["embedding_dtype"]))
            prompts = [VoiceClonePromptItem(code, embedding, False, True, metadata["ref_text"])]
            notice = metadata["notice"]
            self._remember(key, (prompts, notice))
            self._activate(key)
            return prompts, notice, "disk"
        if not reference:
            raise ValueError("저장된 목소리가 없습니다. 녹음을 다시 등록하세요.")
        prompts, notice = build()
        if len(prompts) != 1 or prompts[0].ref_code is None:
            raise ValueError("목소리 등록에 실패했습니다.")
        item = prompts[0]
        metadata = {"namespace": self.namespace, "ref_text": item.ref_text, "notice": notice,
                    "embedding_dtype": str(item.ref_spk_embedding.dtype).split(".")[-1]}
        self.directory.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=self.directory, suffix=".tmp", delete=False) as stream:
            temporary = Path(stream.name)
            np.savez_compressed(stream, metadata=np.array(json.dumps(metadata, ensure_ascii=False)),
                                ref_code=item.ref_code.detach().cpu().numpy(),
                                embedding=item.ref_spk_embedding.detach().float().cpu().numpy())
        os.replace(temporary, location)
        self._remember(key, (prompts, notice))
        self._activate(key)
        return prompts, notice, "created"
