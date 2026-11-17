from unittest.mock import Mock

import os

import pytest

from shop.cart import Cart, Item, RateProvider


def test_empty_cart() -> None:
    cart = Cart()

    assert cart.items_count() == 0
    assert cart.total() == 0.0


def test_add_default_quantity() -> None:
    cart = Cart()

    cart.add("book", price= 200.0)

    assert cart.items_count() == 1
    assert cart.total() == 200.0


def test_items_count(cart_with_items: Cart) -> None:
    assert cart_with_items.items_count() == 6


def test_total(cart_with_items: Cart) -> None:
    assert cart_with_items.total() == 460.0


def test_add_same_product() -> None:
    cart = Cart()
    cart.add("book", price=200.0, qty=2)

    cart.add("book", price=200.0, qty=3)

    assert cart.items_count() == 5
    assert cart.total() == 1000.0


def test_add_same_name_keeps_original_price() -> None:
    cart = Cart()
    cart.add("book", price=200.0)

    cart.add("book", price=300.0)

    assert cart.items_count() == 2
    assert cart.total() == 400.0


def test_add_free_product() -> None:
    cart = Cart()

    cart.add("gift", price=0.0)

    assert cart.items_count() == 1
    assert cart.total() == 0.0


def test_add_negative_price_raises() -> None:
    cart = Cart()

    with pytest.raises(ValueError, match="price"):
        cart.add("book", price=-1.0)


@pytest.mark.parametrize("qty", [0, -1])
def test_add_invalid_quantity_raises(qty: int) -> None:
    cart = Cart()

    with pytest.raises(ValueError, match="qty"):
        cart.add("book", price=200.0, qty=qty)


def test_remove_product(cart_with_items: Cart) -> None:
    cart_with_items.remove("book")

    assert cart_with_items.items_count() == 4
    assert cart_with_items.total() == 60.0


def test_remove_missing_product_raises() -> None:
    cart = Cart()

    with pytest.raises(KeyError, match="missing"):
        cart.remove("missing")


@pytest.mark.parametrize(
    ("discount", "expected"),
    [
        (0.0, 460.0),
        (10.0, 414.0),
        (50.0, 230.0),
        (100.0, 0.0),
    ],
)
def test_total_with_discount(
    cart_with_items: Cart,
    discount: float,
    expected: float,
) -> None:
    result = cart_with_items.total(discount_percent=discount)

    assert result == pytest.approx(expected)


@pytest.mark.parametrize("discount", [-1.0, 101.0])
def test_invalid_discount_raises(
    cart_with_items: Cart,
    discount: float,
) -> None:
    with pytest.raises(ValueError, match="discount_percent"):
        cart_with_items.total(discount_percent=discount)


def test_total_in_usd(cart_with_items: Cart) -> None:
    # Arrange
    rates = Mock(spec=RateProvider)
    rates.get_rate.return_value = 40.0

    # Act
    result = cart_with_items.total_in("USD", rates)

    # Assert
    assert result == pytest.approx(11.5)
    rates.get_rate.assert_called_once_with("USD")


@pytest.mark.parametrize("rate", [0.0, -1.0])
def test_total_in_invalid_rate_raises(
    cart_with_items: Cart,
    rate: float,
) -> None:
    rates = Mock(spec=RateProvider)
    rates.get_rate.return_value = rate

    with pytest.raises(ValueError, match="rate"):
        cart_with_items.total_in("USD", rates)


def test_most_expensive_empty_cart() -> None:
    cart = Cart()

    assert cart.most_expensive() is None


def test_most_expensive_single_product() -> None:
    cart = Cart()
    cart.add("book", price=200.0, qty=2)

    assert cart.most_expensive() == Item("book", 200.0, 2)


def test_most_expensive_uses_unit_price() -> None:
    cart = Cart()
    cart.add("pen", price=15.0, qty=100)
    cart.add("book", price=200.0, qty=1)
    cart.add("notebook", price=50.0, qty=2)

    # Ручки сумарно коштують більше, але книга дорожча за одиницю.
    assert cart.most_expensive() == Item("book", 200.0, 1)
