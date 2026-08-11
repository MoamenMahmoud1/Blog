def serialize_card(card):
    return {
        "id": card.id,
        "title": card.title,
        "content": card.content,
        "order": card.order,
        "is_main": card.parent_id is None,
        "parent_id": card.parent_id,
        "image": card.image.url if card.image else None,
        "video": card.video.url if card.video else None,
    }


def serialize_presentation(presentation):
    return {
        "id": presentation.id,
        "title": presentation.title,
        "cards": [
            {
                **serialize_card(main_card),
                "children": [
                    serialize_card(child) for child in main_card.children.all()
                ],
            }
            for main_card in presentation.main_cards
        ],
    }
