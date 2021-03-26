ckan.module("comments-thread", function ($, _) {
  "use strict";

  return {
    initialize: function () {
      $.proxyAll(this, /_on/);
      this.$(".comment-actions .remove-comment").on(
        "click",
        this._onRemoveComment
      );
      this.$(".comment-actions .approve-comment").on(
        "click",
        this._onApproveComment
      );

      this.$(".comment-form").on("submit", this._onSubmit);
    },
    teardown: function () {
      this.$(".comment-action.remove-comment").off(
        "click",
        this._onRemoveComment
      );
      this.$(".comment-actions .approve-comment").off(
        "click",
        this._onApproveComment
      );

      this.$("comment-form").off("sumbit", this._onSubmit);
    },
    _onRemoveComment: function (e) {
      var id = e.currentTarget.dataset.id;
      this.sandbox.client.call(
        "POST",
        "comments_comment_delete",
        {
          id: id,
        },
        function () {
          window.location.reload();
        }
      );
    },
    _onApproveComment: function (e) {
      var id = e.currentTarget.dataset.id;
      this.sandbox.client.call(
        "POST",
        "comments_comment_approve",
        {
          id: id,
        },
        function () {
          window.location.reload();
        }
      );
    },

    _onSubmit: function (e) {
      e.preventDefault();
      var data = new FormData(e.target);

      this.sandbox.client.call(
        "POST",
        "comments_comment_create",
        {
          content: data.get("content"),
          subject_id: data.get("subject_id"),
          subject_type: data.get("subject_type"),
          create_thread: true,
        },
        function () {
          window.location.reload();
        }
      );
    },
  };
});
