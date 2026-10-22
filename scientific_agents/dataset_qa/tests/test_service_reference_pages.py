"""Source-stable object navigation across pages and multiple deliveries."""
import asyncio
import json

from langchain_core.messages import ToolMessage
import pytest

from ..capabilities import OBJECT
from ..context import encode
from ..contracts import Limits, Options
from ..dialogue import Read
from ..service import DatasetQA
from .test_dataset_qa import action, collect, engine, load, remote, result_cards, session
from .test_decisions import BareDialogue, configured, payload, text
from .test_references import state, stored


@pytest.mark.parametrize("scope", ["candidate", "source"])
@pytest.mark.parametrize("selection", ["focus", "selected", "native"])
def test_hundred_and_first_object_remains_addressable_for_every_selection_path(engine, scope, selection):
    async def run():
        backend, dialogue = configured(), BareDialogue()
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        source = stored(service, sid, "large-source", {"items": [
            {"id": "entry-"+str(index), "title": "Entry "+str(index)} for index in range(120)]})
        handle = scope+":101"
        if scope=="source":
            # The pinned source is not the most recently displayed list.
            stored(service, sid, "another-source", {"items": [{"id": "other", "title": "Other"}]})
        steps = [load()]
        if selection=="focus":
            steps.extend([action("remember", focus=handle), remote("inspect")])
        elif selection=="selected":
            steps.extend([action("remember", selected=[handle]), remote("inspect", **{OBJECT: "selected:1"})])
        else:
            steps.append(remote("inspect", **{OBJECT: handle}))
        dialogue.responses = [*steps, action("deliver_results"), text()]
        try:
            values = await collect(service, sid, "查看指定来源的第101个对象", "navigate", **(
                {"result_id": source["result_id"]} if scope=="source" else {}))
            assert values[-1]["status"]=="COMPLETED"
            assert backend.calls==[("data", "inspect", {"reference": "entry-100"})]
            operation = payload(service, sid, values)["operations"][0]
            assert operation["target"]["result_id"]==source["result_id"]
            assert operation["target"]["path"]=="/items/100"
            if selection=="selected":
                assert state(service, sid)["selected"][0]["path"]=="/items/100"
        finally:
            await service.close()
    asyncio.run(run())


def test_same_turn_page_exposes_stable_executable_handles_beyond_initial_twenty(engine):
    async def run():
        backend, dialogue = configured(), BareDialogue()
        backend.items = [{"id": "entry-"+str(index), "title": "Entry "+str(index)} for index in range(40)]
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        pages = []

        def read_page(messages, definitions):
            source = next(json.loads(message.content)["result_id"] for message in messages
                if isinstance(message, ToolMessage) and message.name.startswith("mcp_")
                and "result_id" in json.loads(message.content))
            return action("read_result", result_id=source, path="/items", offset=20, limit=5)

        def inspect_page(messages, definitions):
            pages.extend(json.loads(message.content) for message in messages
                if isinstance(message, ToolMessage) and message.name=="read_result")
            assert len(pages)==2 and pages[0]["objects"]==pages[1]["objects"]
            assert pages[0]["objects"][0]=={"handle": "object:21", "path": "/items/20"}
            assert [item["id"] for item in pages[0]["data"]]==["entry-"+str(index) for index in range(20, 25)]
            return remote("inspect", **{OBJECT: pages[0]["objects"][0]["handle"]})(messages, definitions)

        dialogue.responses = [load(), remote("search"), read_page, read_page, inspect_page,
            action("deliver_results"), text()]
        try:
            values = await collect(service, sid, "找资源，然后查看第21个的详情", "paged")
            assert values[-1]["status"]=="COMPLETED"
            assert backend.calls==[("data", "search", {}), ("data", "inspect", {"reference": "entry-20"})]
            saved = payload(service, sid, values)
            assert saved["objects"]["object:21"]["path"]=="/items/20"
            assert saved["objects"]["object:21"]["result_id"]==pages[0]["result_id"]
        finally:
            await service.close()
    asyncio.run(run())


def test_mixed_pinned_list_keeps_source_ordinals_in_model_view_and_dispatch(engine):
    async def run():
        backend, dialogue = configured(), BareDialogue()
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        source = stored(service, sid, "mixed", {"items": [None, {"id": "second"}, "note", {"id": "fourth"}]})

        def inspect_fourth(messages, definitions):
            context = json.loads(messages[1].content)
            rows = context["request_objects"]["candidates"]["items"]
            assert [(row["handle"], row["path"]) for row in rows]==[
                ("source:2", "/items/1"), ("source:4", "/items/3")]
            return remote("inspect", **{OBJECT: rows[-1]["handle"]})(messages, definitions)

        dialogue.responses = [load(), inspect_fourth, action("deliver_results"), text()]
        try:
            values = await collect(service, sid, "查看这个来源第四项", "mixed-view", result_id=source["result_id"])
            assert values[-1]["status"]=="COMPLETED"
            assert backend.calls==[("data", "inspect", {"reference": "fourth"})]
        finally:
            await service.close()
    asyncio.run(run())


def test_projected_result_pagination_never_skips_undisplayed_rows(engine):
    async def run():
        backend = configured()
        service = DatasetQA(engine, BareDialogue(), backend.gateway(limits=Limits(result_chars=400)))
        sid = session(service)
        rows = [{"id": "entry-"+str(index), "title": "Resource "+str(index), "description": "long prose "*100}
            for index in range(45)]
        source = stored(service, sid, "large-rows", {"items": rows})
        offset, encountered = 0, []
        try:
            while offset<len(rows):
                page = await service._read_result("alice", sid, Read(result_id=source["result_id"], path="/items", offset=offset, limit=20))
                visible = page["data"]
                assert visible and len(visible)<20
                for index, row in enumerate(visible, offset):
                    assert row.get("id")==rows[index]["id"]
                    encountered.append(row["id"])
                following = offset+len(visible)
                assert page.get("next_offset", len(rows))==following
                offset = following
            assert encountered==[row["id"] for row in rows]
            assert not backend.calls
        finally:
            await service.close()
    asyncio.run(run())


def test_truncated_dictionary_pages_index_omitted_fields_with_readable_escaped_paths(engine):
    async def run():
        backend = configured()
        service = DatasetQA(engine, BareDialogue(), backend.gateway(limits=Limits(result_chars=400)))
        sid = session(service)
        record = {"/field~"+str(index): {"marker": "field-"+str(index), "body": "long prose "*100}
            for index in range(13)}
        source = stored(service, sid, "dictionary", {"record": record})
        offset, indexed, omitted = 0, set(), set()
        try:
            while offset<len(record):
                page = await service._read_result("alice", sid, Read(result_id=source["result_id"], path="/record", offset=offset, limit=8))
                paths = page["field_paths"]
                assert paths and not (indexed & paths.keys())
                omitted.update(set(paths)-set(page.get("data") or {}))
                for key, pointer in paths.items():
                    assert pointer=="/record/"+key.replace("~", "~0").replace("/", "~1")
                    value = await service._read_result("alice", sid, Read(result_id=source["result_id"], path=pointer))
                    assert value["data"]["marker"]==record[key]["marker"]
                indexed.update(paths)
                following = offset+len(paths)
                assert page.get("next_offset", len(record))==following
                offset = following
            assert indexed==set(record) and omitted
            assert not backend.calls
        finally:
            await service.close()
    asyncio.run(run())


def test_public_pagination_redacts_before_field_indexing_and_preserves_empty_redacted_rows(engine):
    async def run():
        backend = configured()
        service = DatasetQA(engine, BareDialogue(), backend.gateway(limits=Limits(result_chars=400)))
        sid = session(service)
        record = {"Password": "hidden-credential"*1000, **{
            "visible-"+str(index): {"marker": str(index), "body": "long prose "*100}
            for index in range(10)}}
        source = stored(service, sid, "sensitive-fields", {"record": record,
            "items": [{"token": "hidden-credential"}, {"id": "visible"}]})
        try:
            directory = await service._read_result("alice", sid, Read(result_id=source["result_id"], path="/record", limit=8))
            assert directory["field_paths"]
            assert all(key.startswith("visible-") for key in directory["field_paths"])
            assert "hidden-credential" not in encode(directory) and "Password" not in encode(directory)
            assert directory["next_offset"]==len(directory["field_paths"])
            # Filtering an inaccessible field creates a real empty row. It must
            # neither fail as a budget placeholder nor shift later array rows.
            first = await service._read_result("alice", sid, Read(result_id=source["result_id"], path="/items", limit=1))
            assert first["data"]==[{}] and first["next_offset"]==1
            second = await service._read_result("alice", sid, Read(result_id=source["result_id"], path="/items", offset=1, limit=1))
            assert second["data"]==[{"id": "visible"}] and "next_offset" not in second
            assert not backend.calls
        finally:
            await service.close()
    asyncio.run(run())


def test_multiple_delivered_lists_preserve_every_source_without_an_arbitrary_candidate_list(engine):
    async def run():
        backend, dialogue = configured(), BareDialogue()
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        stored(service, sid, "older", {"items": [{"id": "stale"}]})

        def search(prefix):
            def response(messages, definitions):
                backend.items = [{"id": prefix+"-record", "title": prefix+" dataset"}]
                return remote("search", query=prefix)(messages, definitions)
            return response

        dialogue.responses = [load(), search("climate"), search("ecology"), action("deliver_results"), text()]
        try:
            values = await collect(service, sid, "分别检索并展示两个领域", "two-lists")
            assert values[-1]["status"]=="COMPLETED"
            cards = result_cards(values)
            assert len(cards)==2
            assert "candidates" not in state(service, sid)
            next_payload = {"message": "比较两份来源", "params": {}, "parent_task_id": None}
            task, _ = service.store.submit("alice", sid, "next-context", next_payload, None, service.owner)
            context, model, _ = await service._context("alice", sid, task["id"], Options())
            assert "candidates" not in context["references"]
            published = model["published_results"]
            assert published["total"]==2
            assert [item["result_id"] for item in published["items"]]==[card["result_id"] for card in cards]
            assert [item["data"]["items"][0]["id"] for item in published["items"]]==["climate-record", "ecology-record"]
            service.store.finish("alice", sid, task["id"], "COMPLETED")
        finally:
            await service.close()
    asyncio.run(run())
